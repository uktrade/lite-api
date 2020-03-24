from copy import deepcopy

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import now
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ErrorDetail
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView

from applications import constants
from applications.creators import validate_application_ready_for_submission
from applications.helpers import (
    get_application_create_serializer,
    get_application_view_serializer,
    get_application_update_serializer,
)
from applications.libraries.application_helpers import (
    optional_str_to_bool,
    can_status_be_set_by_exporter_user,
    can_status_be_set_by_gov_user,
)
from applications.libraries.edit_applications import save_and_audit_have_you_been_informed_ref
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
    PartyOnApplication,
    F680ClearanceApplication,
    Licence,
)
from applications.serializers.exhibition_clearance import ExhibitionClearanceDetailSerializer
from applications.serializers.generic_application import (
    GenericApplicationListSerializer,
    GenericApplicationCopySerializer,
)
from applications.serializers.licence import LicenceSerializer
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.enums import AdviceType, CaseTypeSubTypeEnum, CaseTypeEnum
from cases.sla import get_application_target_sla
from conf.authentication import ExporterAuthentication, SharedAuthentication, GovAuthentication
from conf.constants import ExporterPermissions, GovPermissions
from conf.decorators import authorised_users, application_in_major_editable_state, application_in_editable_state
from conf.helpers import convert_date_to_string
from conf.permissions import assert_user_has_permission
from goodstype.models import GoodsType
from lite_content.lite_api import strings
from organisations.enums import OrganisationType
from organisations.models import Site
from static.f680_clearance_types.enums import F680ClearanceTypeEnum
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.case_status_validate import is_case_status_draft
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.models import ExporterUser
from workflow.flagging_rules_automation import apply_flagging_rules_to_case


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
                case_type_id=CaseTypeEnum.HMRC.id
            )

        return applications

    def post(self, request, **kwargs):
        """
        Create a new application
        """
        data = request.data
        if not data.get("application_type"):
            return JsonResponse(
                data={
                    "errors": {
                        "application_type": [
                            ErrorDetail(string=strings.Applications.Generic.SELECT_AN_APPLICATION_TYPE, code="invalid")
                        ]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        case_type = data.pop("application_type", None)
        serializer = get_application_create_serializer(case_type)
        serializer = serializer(
            data=data, case_type_id=CaseTypeEnum.reference_to_id(case_type), context=request.user.organisation
        )

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
        data = serializer(application, context={"exporter_user": request.user}).data
        return JsonResponse(data=data, status=status.HTTP_200_OK)

    @authorised_users(ExporterUser)
    @application_in_editable_state()
    def put(self, request, application):
        """
        Update an application instance
        """
        serializer = get_application_update_serializer(application)
        case = application.get_case()
        data = request.data.copy()
        serializer = serializer(application, data=data, context=request.user.organisation, partial=True)

        # Prevent minor edits of the goods categories
        if not application.is_major_editable() and request.data.get("goods_categories"):
            return JsonResponse(
                data={"errors": {"goods_categories": [strings.Applications.Generic.NOT_POSSIBLE_ON_MINOR_EDIT]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent minor edits of the clearance level
        if not application.is_major_editable() and request.data.get("clearance_level"):
            return JsonResponse(
                data={"errors": {"clearance_level": [strings.Applications.Generic.NOT_POSSIBLE_ON_MINOR_EDIT]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent minor edits of the f680 clearance types
        if not application.is_major_editable() and request.data.get("types"):
            return JsonResponse(
                data={"errors": {"types": [strings.Applications.Generic.NOT_POSSIBLE_ON_MINOR_EDIT]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent minor edits of additional_information
        if not application.is_major_editable() and any(
            [request.data.get(field) for field in constants.F680.ADDITIONAL_INFORMATION_FIELDS]
        ):
            return JsonResponse(
                data={"errors": {"Additional details": [strings.Applications.Generic.NOT_POSSIBLE_ON_MINOR_EDIT]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if application.case_type.sub_type == CaseTypeSubTypeEnum.HMRC:
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

        if request.data.get("clearance_level"):
            serializer.save()
            return JsonResponse(data={}, status=status.HTTP_200_OK)

        # Audit block
        if application.case_type.sub_type == CaseTypeSubTypeEnum.F680:
            if request.data.get("types"):
                old_types = [
                    F680ClearanceTypeEnum.get_text(type) for type in application.types.values_list("name", flat=True)
                ]
                new_types = [F680ClearanceTypeEnum.get_text(type) for type in request.data.get("types")]
                serializer.save()

                if set(old_types) != set(new_types):
                    audit_trail_service.create(
                        actor=request.user,
                        verb=AuditType.UPDATE_APPLICATION_F680_CLEARANCE_TYPES,
                        target=case,
                        payload={"old_types": old_types, "new_types": new_types},
                    )
                return JsonResponse(data={}, status=status.HTTP_200_OK)
            else:
                serializer.save()

        if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
            save_and_audit_have_you_been_informed_ref(request, application, serializer)

        return JsonResponse(data={}, status=status.HTTP_200_OK)

    @authorised_users(ExporterUser)
    def delete(self, request, application):
        """
        Deleting an application should only be allowed for draft applications
        """
        if not is_case_status_draft(application.status.status):
            return JsonResponse(
                data={"errors": strings.Applications.Generic.DELETE_SUBMITTED_APPLICATION_ERROR},
                status=status.HTTP_400_BAD_REQUEST,
            )
        application.delete()
        return JsonResponse(
            data={"status": strings.Applications.Generic.DELETE_DRAFT_APPLICATION}, status=status.HTTP_200_OK
        )


class ApplicationSubmission(APIView):
    authentication_classes = (ExporterAuthentication,)

    @transaction.atomic
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def put(self, request, application):
        """
        Submit a draft-application which will set its submitted_at datetime and status before creating a case
        """
        if application.case_type.sub_type != CaseTypeSubTypeEnum.HMRC:
            assert_user_has_permission(
                request.user, ExporterPermissions.SUBMIT_LICENCE_APPLICATION, application.organisation
            )
        previous_application_status = application.status

        errors = validate_application_ready_for_submission(application)
        if errors:
            return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        application.submitted_at = timezone.now()
        application.sla_remaining_days = get_application_target_sla(application.case_type.sub_type)
        application.sla_days = 0
        application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        application.save()

        apply_flagging_rules_to_case(application)

        update_submitted_application_good_statuses_and_flags(application)

        # Serialize for the response message
        serializer = get_application_view_serializer(application)
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
        is_licence_application = application.case_type.sub_type != CaseTypeSubTypeEnum.EXHIBITION

        data = deepcopy(request.data)

        if data["status"] == CaseStatusEnum.FINALISED:
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.Finalise.Error.SET_FINALISED]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(request.user, ExporterUser):
            if request.user.organisation.id != application.organisation.id:
                raise PermissionDenied()

            if not can_status_be_set_by_exporter_user(application.status.status, data["status"]):
                return JsonResponse(
                    data={"errors": [strings.Applications.Generic.Finalise.Error.EXPORTER_SET_STATUS]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            if not can_status_be_set_by_gov_user(
                request.user, application.status.status, data["status"], is_licence_application
            ):
                return JsonResponse(
                    data={"errors": [strings.Applications.Generic.Finalise.Error.GOV_SET_STATUS]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if data["status"] == CaseStatusEnum.SURRENDERED:
            if not Licence.objects.filter(application=application, is_complete=True).exists():
                return JsonResponse(
                    data={"errors": [strings.Applications.Generic.Finalise.Error.SURRENDER]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Licence.objects.get(application=application, is_complete=True).delete()

        case_status = get_case_status_by_status(data["status"])
        data["status"] = str(case_status.pk)
        old_status = application.status

        serializer = get_application_update_serializer(application)
        serializer = serializer(application, data=data, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        application = serializer.save()

        if CaseStatusEnum.is_terminal(old_status.status) and not CaseStatusEnum.is_terminal(application.status.status):
            # we reapply flagging rules if the status is reopened from a terminal state
            apply_flagging_rules_to_case(application)

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.UPDATED_STATUS,
            target=application.get_case(),
            payload={"status": CaseStatusEnum.get_text(case_status.status)},
        )

        return JsonResponse(
            data={"data": get_application_view_serializer(application)(application).data}, status=status.HTTP_200_OK
        )


class ApplicationFinaliseView(APIView):
    authentication_classes = (GovAuthentication,)

    @transaction.atomic
    def put(self, request, pk):
        """
        Finalise an application
        """
        application = get_application(pk)
        is_licence_application = application.case_type.sub_type != CaseTypeSubTypeEnum.EXHIBITION
        if not can_status_be_set_by_gov_user(
            request.user, application.status.status, CaseStatusEnum.FINALISED, is_licence_application
        ):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.Finalise.Error.SET_FINALISED]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = deepcopy(request.data)
        action = data.get("action")

        if action == AdviceType.APPROVE:
            default_licence_duration = get_default_duration(application)
            data["duration"] = data.get("duration", default_licence_duration)

            # Check change default duration permission
            if data["duration"] != default_licence_duration and not request.user.has_permission(
                GovPermissions.MANAGE_LICENCE_DURATION
            ):
                return JsonResponse(
                    data={"errors": [strings.Applications.Finalise.Error.SET_DURATION_PERMISSION]},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Create incomplete Licence object
            try:
                start_date = timezone.datetime(year=int(data["year"]), month=int(data["month"]), day=int(data["day"]))
                data["start_date"] = start_date.strftime("%Y-%m-%d")
            except KeyError:
                return JsonResponse(
                    data={"errors": {"start_date": [strings.Applications.Finalise.Error.MISSING_DATE]}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data["application"] = application
            serializer = LicenceSerializer(data=data)

            if not serializer.is_valid():
                return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            return JsonResponse(data=serializer.data, status=status.HTTP_200_OK)

        elif action == AdviceType.REFUSE:
            application.status = get_case_status_by_status(CaseStatusEnum.FINALISED)
            application.save()
            audit_trail_service.create(
                actor=request.user, verb=AuditType.FINALISED_APPLICATION, target=application.get_case(),
            )
            return JsonResponse(data={"application": str(application.id)}, status=status.HTTP_200_OK)

        return JsonResponse(
            data={"errors": [strings.Applications.Finalise.Error.NO_ACTION_GIVEN]}, status=status.HTTP_400_BAD_REQUEST
        )


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
        """
        Copy an application
        In this function we get the application and remove it's relation to itself on the database, which allows for us
        keep most of the data in relation to the application intact.
        """
        self.old_application_id = pk
        old_application = get_application(pk)

        data = request.data

        serializer = GenericApplicationCopySerializer(
            data=data, context={"application_type": old_application.case_type}
        )

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Deepcopy so new_application is not a pointer to old_application
        # (if not deepcopied, any changes done on one applies to the other)
        self.new_application = deepcopy(old_application)

        if self.new_application.case_type.sub_type == CaseTypeSubTypeEnum.F680:
            for field in constants.F680.ADDITIONAL_INFORMATION_FIELDS:
                setattr(self.new_application, field, None)

        # Clear references to parent objects, and current application instance object
        self.strip_id_for_application_copy()

        # Replace the reference and have you been informed (if required) with users answer. Also sets some defaults
        self.new_application.name = request.data["name"]
        self.new_application.have_you_been_informed = request.data.get("have_you_been_informed")
        self.new_application.reference_number_on_information_form = request.data.get(
            "reference_number_on_information_form"
        )
        self.new_application.status = get_case_status_by_status(CaseStatusEnum.DRAFT)
        self.new_application.copy_of_id = self.old_application_id

        # Remove SLA data
        self.new_application.sla_days = 0
        self.new_application.sla_remaining_days = get_application_target_sla(self.new_application.case_type.sub_type)
        self.new_application.last_closed_at = None
        self.new_application.sla_updated_at = None

        # Remove data that should not be copied
        self.remove_data_from_application_copy()

        # Need to save here to create the pk/id for relationships
        self.new_application.save()

        # Create new foreign key connection using data from old application (this is for tables pointing to the case)
        self.create_foreign_relations_for_new_application()
        self.duplicate_goodstypes_for_new_application()

        # Get all parties connected to the application and produce a copy (and replace reference for each one)
        self.duplicate_parties_on_new_application()

        # Get all f680 clearance types
        self.duplicate_f680_clearance_types()

        # Save
        self.new_application.created_at = now()
        self.new_application.save()
        return JsonResponse(data={"data": self.new_application.id}, status=status.HTTP_201_CREATED)

    def strip_id_for_application_copy(self):
        """
        The current object id and pk need removed, and the pointers otherwise save() will determine the object exists
        """
        self.new_application.pk = None
        self.new_application.id = None
        self.new_application.case_ptr = None
        self.new_application.base_application_ptr = None

    def remove_data_from_application_copy(self):
        """
        Removes data of fields that are stored on the case model, and we wish not to copy.
        """
        set_none = [
            "case_officer",
            "reference_code",
            "submitted_at",
            "licence_duration",
            "is_informed_wmd",
            "is_suspected_wmd",
            "is_military_end_use_controls",
            "is_eu_military",
            "is_compliant_limitations_eu",
            "compliant_limitations_eu_ref",
            "intended_end_use",
        ]
        for attribute in set_none:
            setattr(self.new_application, attribute, None)

    def duplicate_parties_on_new_application(self):
        """
        Generates a copy of each party, and recreates any old application Party relations using the new copied party.
        Deleted parties are not copied over.
        """
        party_on_old_application = PartyOnApplication.objects.filter(
            application_id=self.old_application_id, deleted_at__isnull=True
        )
        for old_party_on_app in party_on_old_application:
            old_party_on_app.pk = None
            old_party_on_app.id = None

            # copy party
            old_party_id = old_party_on_app.party.id
            party = old_party_on_app.party
            party.id = None
            party.pk = None
            if not party.copy_of:
                party.copy_of_id = old_party_id
            party.created_at = now()
            party.save()

            old_party_on_app.party = party
            old_party_on_app.application = self.new_application
            old_party_on_app.created_at = now()
            old_party_on_app.save()

    def create_foreign_relations_for_new_application(self):
        """
        Recreates any connections from foreign tables existing on the current application,
         we wish to move to the new application.
        """
        # This is the super set of all many to many related objects for ALL application types.
        # The loop below caters for the possibility that any of the relationships are not relevant to the current
        #  application type
        relationships = [
            GoodOnApplication,
            SiteOnApplication,
            CountryOnApplication,
            ExternalLocationOnApplication,
        ]

        for relation in relationships:
            old_application_relation_results = relation.objects.filter(application_id=self.old_application_id).all()

            for result in old_application_relation_results:
                result.pk = None
                result.id = None
                result.application = self.new_application
                # Some models listed above are not inheriting timestampable models,
                # as such we need to ensure created_at exists
                if getattr(result, "created_at", False):
                    result.created_at = now()
                result.save()

    def duplicate_goodstypes_for_new_application(self):
        """
        Creates a duplicate GoodsType and attaches it to the new application if applicable.
        """
        # GoodsType has more logic than in "create_foreign_relations_for_new_application",
        # such as listing the countries on the goodstype, and flags as such it is seperated.
        for good in GoodsType.objects.filter(application_id=self.old_application_id).all():
            old_good_countries = list(good.countries.all())
            old_good_flags = list(good.flags.all())
            good.pk = None
            good.id = None
            good.application = self.new_application
            good.created_at = now()
            good.save()
            good.countries.set(old_good_countries)
            good.flags.set(old_good_flags)

    def duplicate_f680_clearance_types(self):
        if self.new_application.case_type.sub_type == CaseTypeSubTypeEnum.F680:
            self.new_application.types.set(
                list(
                    F680ClearanceApplication.objects.get(id=self.old_application_id).types.values_list("id", flat=True)
                )
            )


class ExhibitionDetails(ListCreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    queryset = BaseApplication.objects.all()
    serializer = ExhibitionClearanceDetailSerializer

    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        serializer = self.serializer(instance=application, data=request.data)
        if serializer.is_valid():
            old_title = application.title
            old_first_exhibition_date = application.first_exhibition_date
            old_required_by_date = application.required_by_date
            old_reason_for_clearance = application.reason_for_clearance
            case = application.get_case()
            serializer.save()
            validated_data = serializer.validated_data

            if validated_data["title"] != old_title:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UPDATED_EXHIBITION_DETAILS_TITLE,
                    target=case,
                    payload={"old_title": old_title, "new_title": validated_data["title"],},
                )

            if validated_data["first_exhibition_date"] != old_first_exhibition_date:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UPDATED_EXHIBITION_DETAILS_START_DATE,
                    target=application.get_case(),
                    payload={
                        "old_first_exhibition_date": convert_date_to_string(old_first_exhibition_date)
                        if old_first_exhibition_date
                        else "",
                        "new_first_exhibition_date": convert_date_to_string(validated_data["first_exhibition_date"]),
                    },
                )

            if validated_data["required_by_date"] != old_required_by_date:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UPDATED_EXHIBITION_DETAILS_REQUIRED_BY_DATE,
                    target=application.get_case(),
                    payload={
                        "old_required_by_date": convert_date_to_string(old_required_by_date)
                        if old_required_by_date
                        else "",
                        "new_required_by_date": convert_date_to_string(validated_data["required_by_date"]),
                    },
                )

            if validated_data.get("reason_for_clearance") != old_reason_for_clearance:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UPDATED_EXHIBITION_DETAILS_REASON_FOR_CLEARANCE,
                    target=application.get_case(),
                    payload={
                        "old_reason_for_clearance": old_reason_for_clearance,
                        "new_reason_for_clearance": validated_data["reason_for_clearance"],
                    },
                )

            return JsonResponse(data={"application": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
