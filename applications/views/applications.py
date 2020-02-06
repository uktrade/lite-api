from copy import deepcopy

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import now
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
from applications.libraries.goods_on_applications import update_submitted_application_good_statuses_and_flags
from applications.libraries.licence import get_default_duration
from applications.models import (
    BaseApplication,
    HmrcQuery,
    SiteOnApplication,
    GoodOnApplication,
    CountryOnApplication,
    ExternalLocationOnApplication,
)
from applications.serializers.generic_application import (
    GenericApplicationListSerializer,
    GenericApplicationCopySerializer,
)
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.enums import CaseTypeEnum
from conf.authentication import ExporterAuthentication, SharedAuthentication, GovAuthentication
from conf.constants import ExporterPermissions, GovPermissions
from conf.decorators import authorised_users, application_in_major_editable_state, application_in_editable_state
from conf.permissions import assert_user_has_permission
from goodstype.models import GoodsType
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
                data={"errors": strings.Applications.DELETE_SUBMITTED_APPLICATION_ERROR},
                status=status.HTTP_400_BAD_REQUEST,
            )
        application.delete()
        return JsonResponse(data={"status": strings.Applications.DELETE_DRAFT_APPLICATION}, status=status.HTTP_200_OK)


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

        update_submitted_application_good_statuses_and_flags(application)

        # Serialize for the response message
        serializer = get_application_update_serializer(application)
        serializer = serializer(application)

        data = {"application": {"reference_code": application.reference_code, **serializer.data}}

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
            payload={"status": CaseStatusEnum.get_text(case_status.status)},
        )

        return JsonResponse(data={}, status=status.HTTP_200_OK)


class ApplicationFinaliseView(APIView):
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
            data.get("licence_duration") is not None
            and str(data["licence_duration"]) != str(default_licence_duration)
            and not request.user.has_permission(GovPermissions.MANAGE_LICENCE_DURATION)
        ):
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

        return JsonResponse(data=serializer.data, status=status.HTTP_200_OK)


class ApplicationDurationView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Retrieve default duration for an application.
        """
        application = get_application(pk)

        duration = get_default_duration(application)

        return JsonResponse(data={"licence_duration": duration}, status=status.HTTP_200_OK)


class ApplicationCopy(APIView):
    @transaction.atomic
    def post(self, request, pk):
        self.old_application = get_application(pk)

        data = request.data

        serializer = GenericApplicationCopySerializer(
            data=data, context={"application_type": self.old_application.application_type}
        )

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        self.new_application = self.old_application

        #  clear references to parent objects, and current application instance object
        self.strip_id_from_application_copy()

        # replace the reference and have you been informed (if required) with users answer
        self.new_application.name = request.data["name"]
        self.new_application.have_you_been_informed = request.data.get("have_you_been_informed")
        self.new_application.status = get_case_status_by_status(CaseStatusEnum.DRAFT)

        # remove data that should not be copied
        self.remove_data_from_application_copy()

        # need to save here to create the pk/id for relationships
        self.new_application.save()

        # create new many to many connection using data from old application
        self.create_many_to_many_relations_for_new_application()

        # get all parties connected to the application and produce a copy (and replace reference for each one)
        self.update_parties_with_copies()

        # save
        self.new_application.created_at = now()
        self.new_application.save()
        return JsonResponse(data={"data": self.new_application.id}, status=status.HTTP_201_CREATED)

    def strip_id_from_application_copy(self):
        self.new_application.pk = None
        self.new_application.id = None
        self.new_application.case_ptr = None
        self.new_application.base_application_ptr = None

    def remove_data_from_application_copy(self):
        set_none = [
            "case_officer",
            "reference_code",
            "submitted_at",
            "licence_duration",
        ]
        for attribute in set_none:
            setattr(self.new_application, attribute, None)

    def update_parties_with_copies(self):
        foreign_key_party = ["end_user", "consignee"]
        for party_type in foreign_key_party:
            party = getattr(self.old_application, party_type, False)

            if party:
                party.copy_of_id = party.id
                party.pk = None
                party.id = None
                party.created_at = now()
                party.save()
                setattr(self.new_application, party_type, party)

        many_party = ["ultimate_end_users", "third_parties"]
        for party_type in many_party:
            if getattr(self.old_application, party_type, False):
                parties = getattr(self.old_application, party_type).all()

                for party in parties:
                    party.copy_of_id = party.id
                    party.pk = None
                    party.id = None
                    party.created_at = now()
                    party.save()
                    getattr(self.new_application, party_type).add(party)

    def create_many_to_many_relations_for_new_application(self):
        relationships = [
            GoodOnApplication,
            SiteOnApplication,
            CountryOnApplication,
            GoodsType,
            ExternalLocationOnApplication,
        ]

        for relation in relationships:
            relation_objects = relation.objects.filter(application_id=self.old_application.id).all()

            for relation_object in relation_objects:
                relation_object.pk = None
                relation_object.id = None
                relation_object.application_id = self.new_application.id
                # Some models listed above are not inheriting timestampable models,
                # as such we need to ensure created_at exists
                if getattr(relation_object, "created_at", False):
                    relation_object.created_at = now()
                relation_object.save()
