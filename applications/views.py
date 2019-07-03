import json

import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.creators import create_open_licence, create_standard_licence
from applications.enums import ApplicationLicenceType
from applications.libraries.get_application import get_application_by_pk
from applications.models import Application
from applications.serializers import ApplicationBaseSerializer, ApplicationUpdateSerializer
from cases.models import Case
from conf.authentication import PkAuthentication, GovAuthentication
from content_strings.strings import get_string
from drafts.libraries.get_draft import get_draft_with_organisation
from drafts.models import SiteOnDraft, ExternalLocationOnDraft
from gov_users.models import GovUserRevisionMeta
from organisations.libraries.get_organisation import get_organisation_by_user
from queues.models import Queue


class ApplicationList(APIView):
    authentication_classes = (PkAuthentication,)

    def get(self, request):
        """
        List all applications
        """
        organisation = get_organisation_by_user(request.user)

        applications = Application.objects.filter(organisation=organisation).order_by('created_at')
        serializer = ApplicationBaseSerializer(applications, many=True)
        return JsonResponse(data={'applications': serializer.data},
                            )

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
    authentication_classes = (GovAuthentication,)
    """
    Retrieve, update or delete a application instance.
    """

    def get(self, request, pk):
        """
        Retrieve an application instance.
        """
        application = get_application_by_pk(pk)
        serializer = ApplicationBaseSerializer(application)
        return JsonResponse(data={'application': serializer.data})

    def put(self, request, pk):
        """
        Update an application instance.
        """
        with reversion.create_revision():
            serializer = ApplicationUpdateSerializer(get_application_by_pk(pk), data=request.data, partial=True)

            if serializer.is_valid():
                reversion.set_comment("Updated application details")
                reversion.add_meta(GovUserRevisionMeta, gov_user=request.user)
                serializer.save()
                return JsonResponse(data={'application': serializer.data})

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)
