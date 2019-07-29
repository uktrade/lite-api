import json

import reversion
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView

from applications.creators import create_open_licence, create_standard_licence
from applications.enums import ApplicationLicenceType, ApplicationStatus
from applications.libraries.get_application import get_application_by_pk
from applications.models import Application
from applications.serializers import ApplicationBaseSerializer, ApplicationUpdateSerializer, ApplicationCaseNotesSerializer
from cases.models import Case
from conf.authentication import ExporterAuthentication, GovAuthentication
from conf.constants import Permissions
from conf.permissions import has_permission
from content_strings.strings import get_string
from drafts.libraries.get_draft import get_draft_with_organisation
from drafts.models import SiteOnDraft, ExternalLocationOnDraft
from end_user.models import EndUser
from end_user.serializers import EndUserSerializer
from organisations.libraries.get_organisation import get_organisation_by_user
from queues.models import Queue


class ApplicationList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        List all applications
        """
        organisation = get_organisation_by_user(request.user)

        applications = Application.objects.filter(organisation=organisation).order_by('created_at')
        serializer = ApplicationBaseSerializer(applications, many=True)

        return JsonResponse(data={'applications': serializer.data},
                            status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        """
        Create a new application from a draft
        """

        submit_id = json.loads(request.body).get('id')

        with reversion.create_revision():
            # Get Draft
            draft = get_draft_with_organisation(submit_id, get_organisation_by_user(request.user))

            # Create an Application object corresponding to the draft
            application = Application(id=draft.id,
                                      name=draft.name,
                                      activity=draft.activity,
                                      licence_type=draft.licence_type,
                                      export_type=draft.export_type,
                                      reference_number_on_information_form=draft.reference_number_on_information_form,
                                      usage=draft.usage,
                                      created_at=draft.created_at,
                                      last_modified_at=draft.last_modified_at,
                                      organisation=draft.organisation)

            errors = {}

            # Generic errors
            if len(SiteOnDraft.objects.filter(draft=draft)) == 0 \
                    and len(ExternalLocationOnDraft.objects.filter(draft=draft)) == 0:
                errors['location'] = get_string('applications.generic.no_location_set')

            # Create the application depending on type
            if draft.licence_type == ApplicationLicenceType.STANDARD_LICENCE:
                application = create_standard_licence(draft, application, errors)
            elif draft.licence_type == ApplicationLicenceType.OPEN_LICENCE:
                application = create_open_licence(draft, application, errors)

            if not isinstance(application, Application):
                return application

            # Store meta-information.
            reversion.set_user(request.user)
            reversion.set_comment("Created Application Revision")

            # Delete draft
            draft.delete()

            # Create a case
            case = Case(application=application)
            case.save()

            # Add said case to default queue
            queue = Queue.objects.get(pk='00000000-0000-0000-0000-000000000001')
            queue.cases.add(case)
            queue.save()

            serializer = ApplicationBaseSerializer(application)
            return JsonResponse(data={'application': serializer.data},
                                status=status.HTTP_201_CREATED)


class ApplicationDetail(APIView):
    authentication_classes = [GovAuthentication]
    serializer_class = ApplicationBaseSerializer

    """
    Retrieve, update or delete a application instance.
    """

    def get(self, request, pk):
        """
        Retrieve an application instance.
        """
        application = get_application_by_pk(pk)
        serializer = self.serializer_class(application)
        return JsonResponse(data={'application': serializer.data})

    def put(self, request, pk):
        """
        Update an application instance.
        """
        with reversion.create_revision():
            data = json.loads(request.body)

            # Only allow the final decision if the user has the MAKE_FINAL_DECISIONS permission
            if data.get('status') == ApplicationStatus.APPROVED or data.get('status') == ApplicationStatus.DECLINED:
                has_permission(request.user, Permissions.MAKE_FINAL_DECISIONS)

            serializer = ApplicationUpdateSerializer(get_application_by_pk(pk), data=request.data, partial=True)

            if serializer.is_valid():

                # Set audit information
                reversion.set_comment("Updated application details")
                reversion.set_user(self.request.user)

                serializer.save()
                return JsonResponse(data={'application': serializer.data})

            return JsonResponse(data={'errors': serializer.errors}, status=400)


class ApplicationDetailUser(ApplicationDetail):
    authentication_classes = [ExporterAuthentication]
    serializer_class = ApplicationCaseNotesSerializer

    def get(self, request, pk):
        """
        Retrieve an application instance.
        """
        application = get_application_by_pk(pk)
        request.user.notification_set.filter(note__case__application=application).update(
            viewed_at=timezone.now()
        )

        return super(ApplicationDetailUser, self).get(request, pk)


class ApplicationUltimateEndUsers(APIView):
    """
    Set and remove ultimate end users from the draft
    """
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Get ultimate end users associated with a draft
        """
        draft = get_application_by_pk(pk)
        ultimate_end_users_ids = draft.ultimate_end_users.values_list('id', flat=True)
        ultimate_end_users = []
        for id in ultimate_end_users_ids:
            ultimate_end_users.append(EndUser.objects.get(id=str(id)))

        serializer = EndUserSerializer(ultimate_end_users, many=True)

        return JsonResponse(data={'ultimate_end_users': serializer.data},
                            status=status.HTTP_200_OK)
