import json
from datetime import datetime, timezone

import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.creators import validate_standard_licence, validate_open_licence
from applications.enums import ApplicationLicenceType
from applications.libraries.get_applications import get_application
from applications.models import Application, ExternalLocationOnApplication, SiteOnApplication
from applications.serializers import ApplicationBaseSerializer, ApplicationUpdateSerializer
from cases.libraries.activity_types import CaseActivityType
from cases.models import Case, CaseActivity
from conf.authentication import ExporterAuthentication, SharedAuthentication
from conf.constants import Permissions
from conf.permissions import assert_user_has_permission
from content_strings.strings import get_string
from drafts.libraries.get_drafts import get_draft_with_organisation
from organisations.libraries.get_organisation import get_organisation_by_user
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status


class ApplicationList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        List all applications
        """
        organisation = get_organisation_by_user(request.user)

        applications = Application.objects.filter(organisation=organisation).order_by('created_at')
        serializer = ApplicationBaseSerializer(applications, many=True)

        return JsonResponse(data={'applications': serializer.data})

    # @transaction.atomic
    # def post(self, request):
    #     """
    #     Create a new application from a draft
    #     """
    #
    #     submit_id = json.loads(request.body).get('id')
    #
    #     with reversion.create_revision():
    #         # Get Draft
    #         draft = get_draft_with_organisation(submit_id, get_organisation_by_user(request.user))
    #
    #         # Create an Application object corresponding to the draft
    #         application = Application(id=draft.id,
    #                                   name=draft.name,
    #                                   activity=draft.activity,
    #                                   licence_type=draft.licence_type,
    #                                   export_type=draft.export_type,
    #                                   reference_number_on_information_form=draft.reference_number_on_information_form,
    #                                   usage=draft.usage,
    #                                   created_at=draft.created_at,
    #                                   last_modified_at=draft.last_modified_at,
    #                                   organisation=draft.organisation,
    #                                   status=get_case_status_from_status(CaseStatusEnum.SUBMITTED))
    #
    #         errors = {}
    #
    #         # Generic errors
    #         if len(SiteOnDraft.objects.filter(draft=draft)) == 0 \
    #                 and len(ExternalLocationOnDraft.objects.filter(draft=draft)) == 0:
    #             errors['location'] = get_string('applications.generic.no_location_set')
    #
    #         # Create the application depending on type
    #         if draft.licence_type == ApplicationLicenceType.STANDARD_LICENCE:
    #             application = create_standard_licence(draft, application, errors)
    #         elif draft.licence_type == ApplicationLicenceType.OPEN_LICENCE:
    #             application = create_open_licence(draft, application, errors)
    #
    #         if not isinstance(application, Application):
    #             return application
    #
    #         # Store meta-information.
    #         reversion.set_user(request.user)
    #         reversion.set_comment("Created Application Revision")
    #
    #         # Create a case
    #         case = Case(application=application)
    #         case.save()
    #
    #         draft.delete()
    #
    #         serializer = ApplicationBaseSerializer(application)
    #         return JsonResponse(data={'application': {**serializer.data, 'case_id': case.id}},
    #                             status=status.HTTP_201_CREATED)


class ApplicationDetail(APIView):
    authentication_classes = [SharedAuthentication]
    serializer_class = ApplicationBaseSerializer

    """
    Retrieve, update or delete a application instance.
    """

    def get(self, request, pk):
        """
        Retrieve an application instance.
        """
        application = get_application(pk)
        serializer = self.serializer_class(application)
        return JsonResponse(data={'application': serializer.data})

    def put(self, request, pk):
        """
        Update an application instance.
        """
        application = get_application(pk)

        with reversion.create_revision():
            data = json.loads(request.body)

            # Only allow the final decision if the user has the MANAGE_FINAL_ADVICE permission
            if data.get('status') == CaseStatusEnum.FINALISED:
                assert_user_has_permission(request.user, Permissions.MANAGE_FINAL_ADVICE)

            request.data['status'] = str(get_case_status_from_status(data.get('status')).pk)

            serializer = ApplicationUpdateSerializer(get_application(pk), data=request.data, partial=True)

            if serializer.is_valid():
                CaseActivity.create(activity_type=CaseActivityType.UPDATED_STATUS,
                                    case=application.case.get(),
                                    user=request.user,
                                    status=data.get('status'))

                serializer.save()
                return JsonResponse(data={'application': serializer.data})

            return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ApplicationSubmission(APIView):
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        draft = get_draft_with_organisation(pk, get_organisation_by_user(request.user))
        errors = {}

        # Generic errors
        if SiteOnApplication.objects.filter(application=draft).count() == 0 and \
                ExternalLocationOnApplication.objects.filter(application=draft).count() == 0:
            errors['location'] = get_string('applications.generic.no_location_set')

        # Perform additional validation and append errors if found
        if draft.licence_type == ApplicationLicenceType.STANDARD_LICENCE:
            validate_standard_licence(draft, errors)
        elif draft.licence_type == ApplicationLicenceType.OPEN_LICENCE:
            validate_open_licence(draft, errors)

        if errors:
            return JsonResponse(data={'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        # Submit application
        draft.submitted_at = datetime.now(timezone.utc)
        draft.status = get_case_status_from_status(CaseStatusEnum.SUBMITTED)
        draft.save()

        case = Case(application=draft)
        case.save()

        serializer = ApplicationBaseSerializer(draft)
        return JsonResponse(data={'application': {**serializer.data, 'case_id': case.id}},
                            status=status.HTTP_201_CREATED)
