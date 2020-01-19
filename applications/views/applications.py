from copy import deepcopy

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView

from applications.creators import validate_application_ready_for_submission
from applications.enums import ApplicationType
from applications.helpers import (
    get_application_create_serializer,
    get_application_view_serializer,
    get_application_update_serializer,
)
from applications.libraries.application_helpers import (
    optional_str_to_bool,
    can_status_can_be_set_by_exporter_user,
    can_status_can_be_set_by_gov_user,
)
from applications.libraries.get_applications import get_application
from applications.libraries.licence import get_default_duration
from applications.models import GoodOnApplication, BaseApplication, HmrcQuery, SiteOnApplication
from applications.serializers.generic_application import GenericApplicationListSerializer
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.enums import CaseTypeEnum
from conf.authentication import ExporterAuthentication, SharedAuthentication, GovAuthentication
from conf.constants import ExporterPermissions, GovPermissions
from conf.decorators import authorised_users, application_in_major_editable_state, application_in_editable_state
from conf.permissions import assert_user_has_permission
from goods.enums import GoodStatus
from lite_content.lite_api import strings
from organisations.enums import OrganisationType
from organisations.models import Site
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.case_status_validate import is_case_status_draft
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.models import ExporterUser


class ApplicationList(ListCreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = GenericApplicationListSerializer

    def get_serializer_context(self):
        return {"exporter_user": self.request.user}

    def get_queryset(self):
        """
        Filter applications on submitted
        """
        try:
            submitted = optional_str_to_bool(self.request.GET.get("submitted"))
        except ValueError as e:
            return JsonResponse(data={"errors": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if self.request.user.organisation.type == OrganisationType.HMRC:
            if submitted is None:
                applications = HmrcQuery.objects.filter(hmrc_organisation=self.request.user.organisation)
            elif submitted:
                applications = HmrcQuery.objects.submitted(hmrc_organisation=self.request.user.organisation)
            else:
                applications = HmrcQuery.objects.drafts(hmrc_organisation=self.request.user.organisation)
        else:
            if submitted is None:
                applications = BaseApplication.objects.filter(organisation=self.request.user.organisation)
            elif submitted:
                applications = BaseApplication.objects.submitted(self.request.user.organisation)
            else:
                applications = BaseApplication.objects.drafts(self.request.user.organisation)

            users_sites = Site.objects.get_by_user_and_organisation(self.request.user, self.request.user.organisation)
            disallowed_applications = SiteOnApplication.objects.exclude(site__id__in=users_sites).values_list(
                "application", flat=True
            )
            applications = applications.exclude(id__in=disallowed_applications).exclude(
                application_type=ApplicationType.HMRC_QUERY
            )

        return applications

    def post(self, request, **kwargs):
        """
        Create a new application
        Types include StandardApplication, OpenApplication and HmrcQuery
        """
        data = request.data
        serializer = get_application_create_serializer(data.get("application_type"))
        serializer = serializer(data=data, context=request.user.organisation)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        application = serializer.save()

        return JsonResponse(data={"id": application.id}, status=status.HTTP_201_CREATED)


class ApplicationDetail(RetrieveUpdateDestroyAPIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        Retrieve an application instance
        """
        serializer = get_application_view_serializer(application)
        serializer = serializer(application, context={"exporter_user": request.user})
        return JsonResponse(data=serializer.data, status=status.HTTP_200_OK)

    @authorised_users(ExporterUser)
    @application_in_editable_state()
    def put(self, request, application):
        """
        Update an application instance
        """
        serializer = get_application_update_serializer(application)
        case = application.get_case()
        serializer = serializer(application, data=request.data, context=request.user.organisation, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if application.application_type == ApplicationType.HMRC_QUERY:
            serializer.save()

            return JsonResponse(data={}, status=status.HTTP_200_OK)

        # Audit block
        if request.data.get("name"):
            old_name = application.name

            serializer.save()

            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.UPDATED_APPLICATION_NAME,
                target=case,
                payload={"old_name": old_name, "new_name": serializer.data.get("name")},
            )
            return JsonResponse(data={}, status=status.HTTP_200_OK)

        # Audit block
        if application.application_type == ApplicationType.STANDARD_LICENCE:
            old_have_you_been_informed = application.have_you_been_informed == "yes"
            have_you_been_informed = request.data.get("have_you_been_informed") == "yes"

            old_ref_number = application.reference_number_on_information_form or "no reference"
            serializer.save()
            new_ref_number = application.reference_number_on_information_form or "no reference"

            if old_have_you_been_informed and not have_you_been_informed:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.REMOVED_APPLICATION_LETTER_REFERENCE,
                    target=case,
                    payload={"old_ref_number": old_ref_number},
                )
            else:
                if old_have_you_been_informed:
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.UPDATE_APPLICATION_LETTER_REFERENCE,
                        target=case,
                        payload={"old_ref_number": old_ref_number, "new_ref_number": new_ref_number},
                    )
                else:
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.ADDED_APPLICATION_LETTER_REFERENCE,
                        target=case,
                        payload={"new_ref_number": new_ref_number},
                    )

        return JsonResponse(data={}, status=status.HTTP_200_OK)

    @authorised_users(ExporterUser)
    def delete(self, request, application):
        """
        Deleting an application should only be allowed for draft applications
        """
        if not is_case_status_draft(application.status.status):
            return JsonResponse(
                data={"errors": "Only draft applications can be deleted"}, status=status.HTTP_400_BAD_REQUEST
            )
        application.delete()
        return JsonResponse(data={"status": "Draft application deleted"}, status=status.HTTP_200_OK)


class ApplicationSubmission(APIView):
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def put(self, request, application):
        """
        Submit a draft-application which will set its submitted_at datetime and status before creating a case
        """
        if application.application_type != CaseTypeEnum.HMRC_QUERY:
            assert_user_has_permission(
                request.user, ExporterPermissions.SUBMIT_LICENCE_APPLICATION, application.organisation
            )
        previous_application_status = application.status

        errors = validate_application_ready_for_submission(application)
        if errors:
            return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        application.submitted_at = timezone.now()
        application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        application.save()

        if application.application_type == ApplicationType.STANDARD_LICENCE:
            for good_on_application in GoodOnApplication.objects.filter(application=application):
                if good_on_application.good.status == GoodStatus.DRAFT:
                    good_on_application.good.status = GoodStatus.SUBMITTED
                    good_on_application.good.save()

        # Serialize for the response message
        serializer = get_application_update_serializer(application)
        serializer = serializer(application)

        data = {"application": {**serializer.data}}

        if not is_case_status_draft(previous_application_status.status):
            # Only create the audit if the previous application status was not `Draft`
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.UPDATED_STATUS,
                target=application.get_case(),
                payload={"status": application.status.status},
            )

        return JsonResponse(data=data, status=status.HTTP_200_OK)


class ApplicationManageStatus(APIView):
    authentication_classes = (SharedAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        application = get_application(pk)

        data = deepcopy(request.data)

        if data["status"] == CaseStatusEnum.FINALISED:
            return JsonResponse(
                data={"errors": [strings.Applications.Finalise.Error.SET_FINALISED]}, status=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(request.user, ExporterUser):
            if request.user.organisation.id != application.organisation.id:
                raise PermissionDenied()

            if not can_status_can_be_set_by_exporter_user(application.status.status, data["status"]):
                return JsonResponse(
                    data={"errors": [strings.Applications.Finalise.Error.SET_STATUS]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            if not can_status_can_be_set_by_gov_user(request.user, application.status.status, data["status"]):
                return JsonResponse(
                    data={"errors": [strings.Applications.Finalise.Error.SET_STATUS]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        case_status = get_case_status_by_status(data["status"])
        data["status"] = str(case_status.pk)

        serializer = get_application_update_serializer(application)
        serializer = serializer(application, data=data, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.UPDATED_STATUS,
            target=application.get_case(),
            payload={"status": CaseStatusEnum.human_readable(case_status.status)},
        )

        return JsonResponse(data={}, status=status.HTTP_200_OK)


class FinaliseView(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        """
        Finalise an application
        """
        application = get_application(pk)
        if not can_status_can_be_set_by_gov_user(request.user, application.status.status, CaseStatusEnum.FINALISED):
            return JsonResponse(
                data={"errors": [strings.Applications.Finalise.Error.SET_FINALISED]}, status=status.HTTP_400_BAD_REQUEST
            )

        data = deepcopy(request.data)

        default_licence_duration = get_default_duration(application)

        if (
                data.get("licence_duration") is not None and
                data["licence_duration"] != default_licence_duration and
                not request.user.has_permission(GovPermissions.MANAGE_LICENCE_DURATION)
        ):
            #
            return JsonResponse(
                data={"errors": [strings.Applications.Finalise.Error.SET_DURATION_PERMISSION]},
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            data["licence_duration"] = data.get("licence_duration", default_licence_duration)

        data["status"] = str(get_case_status_by_status(CaseStatusEnum.FINALISED).pk)

        serializer_cls = get_application_update_serializer(application)
        serializer = serializer_cls(application, data=data, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.FINALISED_APPLICATION,
            target=application.get_case(),
            payload={"licence_duration": serializer.validated_data["licence_duration"]},
        )

        return JsonResponse(data={}, status=status.HTTP_200_OK)


class DurationView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieve default duration for an application.
        """
        application = get_application(pk)

        duration = get_default_duration(application)

        return JsonResponse(data={"licence_duration": duration}, status=status.HTTP_200_OK)
