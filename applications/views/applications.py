from copy import deepcopy

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.timezone import now
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ErrorDetail
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, UpdateAPIView
from rest_framework.views import APIView

from applications import constants
from applications.creators import validate_application_ready_for_submission, _validate_agree_to_declaration
from applications.helpers import (
    get_application_create_serializer,
    get_application_view_serializer,
    get_application_update_serializer,
)
from applications.libraries.application_helpers import (
    optional_str_to_bool,
    can_status_be_set_by_exporter_user,
    can_status_be_set_by_gov_user,
    create_submitted_audit,
)
from applications.libraries.case_status_helpers import set_application_sla
from applications.libraries.edit_applications import (
    save_and_audit_have_you_been_informed_ref,
    set_case_flags_on_submitted_standard_or_open_application,
)
from applications.libraries.get_applications import get_application
from applications.libraries.goods_on_applications import add_goods_flags_to_submitted_application
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
)
from licences.models import Licence
from applications.serializers.exhibition_clearance import ExhibitionClearanceDetailSerializer
from applications.serializers.generic_application import (
    GenericApplicationListSerializer,
    GenericApplicationCopySerializer,
)
from applications.serializers.good import (
    GoodOnApplicationLicenceQuantitySerializer,
    GoodOnApplicationLicenceQuantityCreateSerializer,
)
from licences.serializers.create_licence import LicenceCreateSerializer
from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from cases.enums import AdviceType, CaseTypeSubTypeEnum, CaseTypeEnum
from cases.libraries.get_flags import get_flags
from cases.models import FinalAdvice
from cases.sla import get_application_target_sla
from cases.serializers import SimpleFinalAdviceSerializer
from conf.authentication import ExporterAuthentication, SharedAuthentication, GovAuthentication
from conf.constants import ExporterPermissions, GovPermissions
from conf.decorators import (
    authorised_users,
    application_in_major_editable_state,
    application_in_editable_state,
    allowed_application_types,
)
from conf.helpers import convert_date_to_string, str_to_bool
from conf.permissions import assert_user_has_permission
from flags.enums import FlagStatuses
from goodstype.models import GoodsType
from lite_content.lite_api import strings
from organisations.enums import OrganisationType
from organisations.libraries.get_organisation import get_request_user_organisation, get_request_user_organisation_id
from organisations.models import Site
from static.f680_clearance_types.enums import F680ClearanceTypeEnum
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.case_status_validate import is_case_status_draft
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.models import ExporterUser
from workflow.automation import run_routing_rules
from workflow.flagging_rules_automation import apply_flagging_rules_to_case


class ApplicationList(ListCreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = GenericApplicationListSerializer

    def get_serializer_context(self):
        return {"exporter_user": self.request.user, "organisation_id": get_request_user_organisation_id(self.request)}

    def get_queryset(self):
        """
        Filter applications on submitted
        """
        try:
            submitted = optional_str_to_bool(self.request.GET.get("submitted"))
        except ValueError as e:
            return JsonResponse(data={"errors": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        organisation = get_request_user_organisation(self.request)

        if organisation.type == OrganisationType.HMRC:
            if submitted is None:
                applications = HmrcQuery.objects.filter(hmrc_organisation=organisation)
            elif submitted:
                applications = HmrcQuery.objects.submitted(hmrc_organisation=organisation)
            else:
                applications = HmrcQuery.objects.drafts(hmrc_organisation=organisation)
        else:
            if submitted is None:
                applications = BaseApplication.objects.filter(organisation=organisation)
            elif submitted:
                applications = BaseApplication.objects.submitted(organisation)
            else:
                applications = BaseApplication.objects.drafts(organisation)

            users_sites = Site.objects.get_by_user_and_organisation(self.request.user, organisation)
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
            data=data,
            case_type_id=CaseTypeEnum.reference_to_id(case_type),
            context=get_request_user_organisation(request),
        )

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        application = serializer.save()

        return JsonResponse(data={"id": application.id}, status=status.HTTP_201_CREATED)


class ApplicationExisting(APIView):
    """
    This view returns boolean values depending on the type of organisation:
    HMRC - Whether the organisation has existing submitted queries
    Standard - Whether the organisation has any drafts/applications, or licences
    """

    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        organisation = get_request_user_organisation(request)
        if organisation.type == "hmrc":
            has_queries = HmrcQuery.objects.submitted(hmrc_organisation=organisation).exists()
            return JsonResponse(data={"queries": has_queries})
        else:
            has_licences = Licence.objects.filter(application__organisation=organisation).exists()
            has_applications = BaseApplication.objects.filter(organisation=organisation).exists()
            return JsonResponse(data={"licences": has_licences, "applications": has_applications})


class ApplicationDetail(RetrieveUpdateDestroyAPIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        Retrieve an application instance
        """
        serializer = get_application_view_serializer(application)
        data = serializer(
            application,
            context={
                "user_type": request.user.type,
                "exporter_user": request.user,
                "organisation_id": get_request_user_organisation_id(request),
            },
        ).data
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
        serializer = serializer(application, data=data, context=get_request_user_organisation(request), partial=True)

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
        Submit a draft application which will set its submitted_at datetime and status before creating a case
        Depending on the application subtype, this will also submit the declaration of the licence
        """
        old_status = application.status.status

        if application.case_type.sub_type != CaseTypeSubTypeEnum.HMRC:
            assert_user_has_permission(
                request.user, ExporterPermissions.SUBMIT_LICENCE_APPLICATION, application.organisation
            )

        errors = validate_application_ready_for_submission(application)
        if errors:
            return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # Queries are completed directly when submit is clicked on the task list
        # HMRC are completed when submit is clicked on the summary page (page after task list)
        # Applications are completed when submit is clicked on the declaration page (page after summary page)

        if application.case_type.sub_type in [CaseTypeSubTypeEnum.EUA, CaseTypeSubTypeEnum.GOODS,] or (
            CaseTypeSubTypeEnum.HMRC and request.data.get("submit_hmrc")
        ):
            set_application_sla(application)
            create_submitted_audit(request, application, old_status)

        if application.case_type.sub_type in [
            CaseTypeSubTypeEnum.STANDARD,
            CaseTypeSubTypeEnum.OPEN,
            CaseTypeSubTypeEnum.F680,
            CaseTypeSubTypeEnum.GIFTING,
            CaseTypeSubTypeEnum.EXHIBITION,
        ]:
            if request.data.get("submit_declaration"):
                errors = _validate_agree_to_declaration(request, errors)
                if errors:
                    return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

                # If a valid declaration is provided, save the application
                application.agreed_to_foi = request.data.get("agreed_to_foi")
                set_application_sla(application)

                if application.case_type.sub_type in [CaseTypeSubTypeEnum.STANDARD, CaseTypeSubTypeEnum.OPEN]:
                    set_case_flags_on_submitted_standard_or_open_application(application)

                add_goods_flags_to_submitted_application(application)
                apply_flagging_rules_to_case(application)
                create_submitted_audit(request, application, old_status)
                run_routing_rules(application)

        # Serialize for the response message
        serializer = get_application_view_serializer(application)
        serializer = serializer(application, context={"user_type": request.user.type})

        data = {"application": {"reference_code": application.reference_code, **serializer.data}}

        if application.reference_code:
            data["reference_code"] = application.reference_code

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
            if get_request_user_organisation_id(request) != application.organisation.id:
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
            payload={"status": {"new": CaseStatusEnum.get_text(case_status.status), "old": old_status.status}},
        )

        # Case routing rules
        if old_status != application.status:
            run_routing_rules(case=application, keep_status=True)

        return JsonResponse(
            data={
                "data": get_application_view_serializer(application)(
                    application, context={"user_type": request.user.type}
                ).data
            },
            status=status.HTTP_200_OK,
        )


class ApplicationFinaliseView(APIView):
    authentication_classes = (GovAuthentication,)
    approved_goods_advice = None
    approved_goods_on_application = None

    def dispatch(self, request, *args, **kwargs):
        self.approved_goods_advice = FinalAdvice.objects.filter(
            case_id=kwargs["pk"], type__in=[AdviceType.APPROVE, AdviceType.PROVISO], good_id__isnull=False,
        )
        self.approved_goods_on_application = GoodOnApplication.objects.filter(
            application_id=kwargs["pk"], good__in=self.approved_goods_advice.values_list("good", flat=True)
        )
        return super(ApplicationFinaliseView, self).dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        """
        Get goods to set licenced quantity for, with advice
        """
        goods_on_application = GoodOnApplicationLicenceQuantitySerializer(
            self.approved_goods_on_application, many=True
        ).data

        for good_advice in self.approved_goods_advice:
            for good in goods_on_application:
                if str(good_advice.good.id) == good["good"]["id"]:
                    good["advice"] = SimpleFinalAdviceSerializer(good_advice).data

        return JsonResponse({"goods": goods_on_application})

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

        if action in [AdviceType.APPROVE, AdviceType.PROVISO]:
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

            # Check if any blocking flags are on the case
            blocking_flags = (
                get_flags(application.get_case())
                .filter(status=FlagStatuses.ACTIVE, blocks_approval=True)
                .order_by("name")
                .values_list("name", flat=True)
            )
            if blocking_flags:
                raise PermissionDenied(
                    [f"{strings.Applications.Finalise.Error.BLOCKING_FLAGS}{','.join(list(blocking_flags))}"]
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

            # Check goods have licenced quantity/value
            if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
                errors = {}
                for good in self.approved_goods_on_application:
                    good_id = str(good.id)
                    quantity_key = f"quantity-{good_id}"
                    value_key = f"value-{good_id}"
                    good_data = {
                        "licenced_quantity": request.data.get(quantity_key),
                        "licenced_value": request.data.get(value_key),
                    }
                    serializer = GoodOnApplicationLicenceQuantityCreateSerializer(good, data=good_data, partial=True)

                    if serializer.is_valid():
                        serializer.save()
                    else:
                        quantity_error = serializer.errors.get("licenced_quantity")
                        if quantity_error:
                            errors[quantity_key] = quantity_error
                        value_error = serializer.errors.get("licenced_value")
                        if value_error:
                            errors[value_key] = value_error

                if errors:
                    return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

            data["application"] = application
            serializer = LicenceCreateSerializer(data=data)

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
        if (
            self.new_application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD
            and not self.new_application.case_type.id == CaseTypeEnum.SICL.id
        ):
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

        # Remove usage & licenced quantity/ value
        self.new_application.goods.update(usage=0, licenced_quantity=None, licenced_value=None)
        self.new_application.goods_type.update(usage=0)

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
            "informed_wmd_ref",
            "is_suspected_wmd",
            "suspected_wmd_ref",
            "is_military_end_use_controls",
            "military_end_use_controls_ref",
            "is_eu_military",
            "is_compliant_limitations_eu",
            "compliant_limitations_eu_ref",
            "is_shipped_waybill_or_lading",
            "non_waybill_or_lading_route_details",
            "intended_end_use",
            "temp_export_details",
            "is_temp_direct_control",
            "temp_direct_control_details",
            "proposed_return_date",
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
            old_good_control_list_entries = list(good.control_list_entries.all())
            good.pk = None
            good.id = None
            good.application = self.new_application
            good.created_at = now()
            good.save()
            good.countries.set(old_good_countries)
            good.flags.set(old_good_flags)
            good.control_list_entries.set(old_good_control_list_entries)

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


class ApplicationRouteOfGoods(UpdateAPIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    @application_in_major_editable_state()
    @allowed_application_types([CaseTypeSubTypeEnum.OPEN, CaseTypeSubTypeEnum.STANDARD])
    def put(self, request, application):
        """ Update an application instance with route of goods data. """

        serializer = get_application_update_serializer(application)
        case = application.get_case()
        data = request.data.copy()

        serializer = serializer(application, data=data, context=get_request_user_organisation(request), partial=True)
        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        previous_answer = application.is_shipped_waybill_or_lading
        new_answer = str_to_bool(data.get("is_shipped_waybill_or_lading"))

        if previous_answer != new_answer:
            self.add_audit_entry(request, case, "is shipped waybill or lading", previous_answer, new_answer)

        if not new_answer:
            previous_details = application.non_waybill_or_lading_route_details
            new_details = data.get("non_waybill_or_lading_route_details")

            if previous_details != new_details:
                self.add_audit_entry(
                    request, case, "non_waybill_or_lading_route_details", previous_details, new_details
                )

        serializer.save()
        return JsonResponse(data={}, status=status.HTTP_200_OK)

    @staticmethod
    def add_audit_entry(request, case, field, previous_value, new_value):
        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.UPDATED_ROUTE_OF_GOODS,
            target=case,
            payload={"route_of_goods_field": field, "previous_value": previous_value, "new_value": new_value},
        )
