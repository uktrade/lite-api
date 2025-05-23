from collections import defaultdict
from datetime import timedelta

from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils import timezone

from rest_framework import serializers

from api.appeals.constants import APPEAL_DAYS
from api.cases.enums import AdviceLevel, AdviceType, CaseTypeSubTypeEnum
from api.compliance.enums import ComplianceVisitTypes, ComplianceRiskValues
from api.licences.enums import LicenceStatus
from api.parties.enums import PartyRole, PartyType, SubType
from api.staticdata.denial_reasons.serializers import DenialReasonSerializer
from api.staticdata.units.enums import Units
from api.goods.enums import (
    PvGrading,
    ItemCategory,
    Component,
    MilitaryUse,
    GoodControlled,
    GoodPvGraded,
)

from api.applications.models import (
    BaseApplication,
    ApplicationDocument,
    StandardApplication,
    GoodOnApplication,
)
from api.goods.models import PvGradingDetails, Good, FirearmGoodDetails
from api.cases.models import Advice, EcjuQuery, CaseNote, Case, CaseType
from api.organisations.models import Organisation
from api.addresses.models import Address
from api.parties.models import Party
from api.compliance.models import ComplianceVisitCase, CompliancePerson
from api.licences.models import Licence
from api.organisations.models import Site, ExternalLocation
from api.queries.end_user_advisories.models import EndUserAdvisoryQuery
from api.queries.goods_query.models import GoodsQuery
from api.f680.caseworker.serializers import SecurityReleaseOutcomeLetterSerializer
from api.f680.models import SecurityReleaseOutcome
from api.f680.enums import SecurityReleaseOutcomes

from api.staticdata.countries.models import Country

from lite_routing.routing_rules_internal.enums import QueuesEnum

from api.core.helpers import (
    get_date_and_time,
    add_months,
    DATE_FORMAT,
    TIME_FORMAT,
    friendly_boolean,
    pluralise_unit,
    get_value_from_enum,
)

from api.staticdata.statuses.libraries.get_case_status import get_status_value_from_case_status_enum


class FriendlyBooleanField(serializers.Field):
    def to_representation(self, value):
        return friendly_boolean(value)

    def to_internal_value(self, data):
        if data is None or data == "":
            return None
        elif data == "Yes":
            return True
        elif data == "No":
            return False
        else:
            return False


class CaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseType
        fields = ["type", "sub_type", "reference"]


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["name", "code"]

    code = serializers.CharField(source="id")


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["address_line_1", "address_line_2", "postcode", "city", "region", "country"]

    address_line_1 = serializers.SerializerMethodField()
    country = CountrySerializer()

    def get_address_line_1(self, obj):
        return obj.address_line_1 or obj.address


class AddresseeSerializer(serializers.Serializer):
    name = serializers.SerializerMethodField()
    email = serializers.CharField()
    address = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()

    def get_name(self, obj):
        if hasattr(obj, "first_name"):
            return " ".join([obj.first_name, obj.last_name])
        return obj.name

    def get_address(self, obj):
        if hasattr(obj, "address"):
            return obj.address
        return None

    def get_phone_number(self, obj):
        if hasattr(obj, "phone_number"):
            return obj.phone_number
        return None


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ["name", "address"]

    address = AddressSerializer()


class FlattenedSiteSerializer(SiteSerializer):
    def to_representation(self, obj):
        ret = super().to_representation(obj)
        ret = {**ret, **ret["address"]}
        del ret["address"]
        return ret


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ["name", "eori_number", "sic_number", "vat_number", "registration_number", "primary_site"]

    primary_site = FlattenedSiteSerializer()


class LicenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licence
        fields = ["duration", "start_date", "end_date", "reference_code"]

    start_date = serializers.DateField(format=DATE_FORMAT, input_formats=None)
    end_date = serializers.SerializerMethodField()

    def get_end_date(self, obj):
        return add_months(obj.start_date, obj.duration)


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ["type", "name", "address", "descriptors", "website", "country", "clearance_level", "role"]

    type = serializers.SerializerMethodField()
    country = CountrySerializer()
    clearance_level = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    def get_role(self, obj):
        if obj.type == PartyType.THIRD_PARTY:
            return obj.role_other if obj.role_other else get_value_from_enum(obj.role, PartyRole)
        return None

    def get_clearance_level(self, obj):
        return PvGrading.to_str(obj.clearance_level) if obj.clearance_level else None

    def get_type(self, obj):
        return obj.sub_type_other if obj.sub_type_other else get_value_from_enum(obj.sub_type, SubType)


class CaseNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseNote
        fields = ["text", "is_visible_to_exporter", "time", "date", "user"]

    user = serializers.SerializerMethodField()
    date = serializers.DateTimeField(format=DATE_FORMAT, input_formats=None, source="created_at")
    time = serializers.DateTimeField(format=TIME_FORMAT, input_formats=None, source="created_at")

    def get_user(self, obj):
        return " ".join([obj.user.first_name, obj.user.last_name])


class ExternalLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalLocation
        fields = ["name", "address", "country"]

    country = CountrySerializer()


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = ["id", "name", "description"]


class EcjuQueryQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcjuQuery
        fields = ["text", "user", "created_at", "raised_by_user", "question", "date", "time"]

    text = serializers.CharField(source="question")
    user = serializers.SerializerMethodField()
    date = serializers.DateTimeField(format=DATE_FORMAT, input_formats=None, source="created_at")
    time = serializers.DateTimeField(format=TIME_FORMAT, input_formats=None, source="created_at")

    def get_user(self, obj):
        return f"{obj.raised_by_user.first_name} {obj.raised_by_user.last_name}"


class EcjuQueryResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcjuQuery
        fields = ["text", "user", "created_at", "responded_by_user", "response", "date", "time"]

    text = serializers.CharField(source="response")
    user = serializers.SerializerMethodField()
    date = serializers.DateTimeField(format=DATE_FORMAT, input_formats=None, source="created_at")
    time = serializers.DateTimeField(format=TIME_FORMAT, input_formats=None, source="created_at")

    def get_user(self, obj):
        if obj.responded_by_user:
            return f"{obj.responded_by_user.first_name} {obj.responded_by_user.last_name}"
        else:
            return "N/A"


class EcjuQuerySerializer(serializers.Serializer):
    def to_representation(self, obj):
        ret = super().to_representation(obj)
        question = EcjuQueryQuestionSerializer(obj).data
        response = EcjuQueryResponseSerializer(obj).data
        ret["question"] = question
        ret["response"] = response
        return ret


class BaseApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseApplication
        fields = [
            "user_reference",
            "end_use_details",
            "military_end_use_controls_reference",
            "military_end_use_controls",
            "informed_wmd",
            "suspected_wmd",
            "suspected_wmd_reference",
            "informed_wmd_reference",
            "eu_military",
            "compliant_limitations_eu_reference",
            "compliant_limitations_eu",
        ]

    user_reference = serializers.CharField(source="name")
    end_use_details = serializers.CharField(source="intended_end_use")
    military_end_use_controls_reference = serializers.CharField(source="military_end_use_controls_ref")
    military_end_use_controls = FriendlyBooleanField(source="is_military_end_use_controls")
    informed_wmd = FriendlyBooleanField(source="is_informed_wmd")
    informed_wmd_reference = serializers.CharField(source="informed_wmd_ref")
    suspected_wmd = FriendlyBooleanField(source="is_suspected_wmd")
    suspected_wmd_reference = serializers.CharField(source="suspected_wmd_ref")
    informed_wmd_reference = serializers.CharField(source="informed_wmd_ref")
    eu_military = FriendlyBooleanField(source="is_eu_military")
    compliant_limitations_eu = FriendlyBooleanField(source="is_compliant_limitations_eu")
    compliant_limitations_eu_reference = serializers.CharField(source="compliant_limitations_eu_ref")


class TemporaryExportDetailsSerializer(serializers.Serializer):
    """
    Serializes StandardApplication
    """

    temp_export_details = serializers.CharField()
    is_temp_direct_control = FriendlyBooleanField()
    temp_direct_control_details = serializers.CharField()
    proposed_return_date = serializers.DateField(format=DATE_FORMAT, input_formats=None)


class StandardApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StandardApplication
        fields = [
            "export_type",
            "reference_number_on_information_form",
            "has_been_informed",
            "shipped_waybill_or_lading",
            "non_waybill_or_lading_route_details",
            "proposed_return_date",
            "trade_control_activity",
            "trade_control_activity_other",
            "trade_control_product_categories",
            "temporary_export_details",
        ]

    has_been_informed = serializers.CharField(source="have_you_been_informed")
    shipped_waybill_or_lading = FriendlyBooleanField(source="is_shipped_waybill_or_lading")
    proposed_return_date = serializers.DateField(format=DATE_FORMAT, input_formats=None)
    temporary_export_details = serializers.SerializerMethodField()

    def get_temporary_export_details(self, obj):
        return TemporaryExportDetailsSerializer(obj).data


class FlattenedStandardApplicationSerializer(StandardApplicationSerializer):
    class Meta:
        model = Case
        fields = ["baseapplication"]

    baseapplication = BaseApplicationSerializer()

    def to_representation(self, obj):
        ret = super().to_representation(obj)
        standard_application = StandardApplication.objects.get(id=obj.pk)
        standard_application_data = StandardApplicationSerializer(standard_application).data
        serialized = {**ret["baseapplication"], **standard_application_data}
        return serialized


class EndUserAdvisoryQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = EndUserAdvisoryQuery
        fields = [
            "note",
            "query_reason",
            "nature_of_business",
            "contact_name",
            "contact_email",
            "contact_job_title",
            "contact_telephone",
            "end_user",
        ]

    query_reason = serializers.CharField(source="reasoning")
    end_user = PartySerializer()


class EndUserAdvisoryQueryCaseSerializer(serializers.Serializer):
    def to_representation(self, obj):
        ret = super().to_representation(obj)
        end_user_advisory = EndUserAdvisoryQuery.objects.get(id=obj.pk)
        serialized = {**ret, **EndUserAdvisoryQuerySerializer(end_user_advisory).data}
        return serialized


class PvGradingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PvGradingDetails
        fields = ["prefix", "suffix", "issuing_authority", "reference", "date_of_issue", "grading"]

    grading = serializers.SerializerMethodField()

    def get_grading(self, obj):
        if obj.grading:
            return PvGrading.to_str(obj.grading)
        return obj.custom_grading


class GoodsQueryGoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = ["description", "name", "control_list_entries", "is_controlled", "part_number"]

    is_controlled = serializers.BooleanField(source="is_good_controlled", allow_null=True)
    control_list_entries = serializers.SerializerMethodField()

    def get_control_list_entries(self, obj):
        return [clc.rating for clc in obj.control_list_entries.all()]


class FirearmDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirearmGoodDetails
        fields = [
            "type",
            "year_of_manufacture",
            "calibre",
            "is_covered_by_firearm_act_section_one_two_or_five",
            "firearms_act_section",
            "section_certificate_number",
            "section_certificate_date_of_expiry",
            "has_serial_numbers",
            "no_identification_markings_details",
            "serial_numbers_available",
            "number_of_items",
            "serial_numbers",
        ]

    section_certificate_date_of_expiry = serializers.DateField(format=DATE_FORMAT, input_formats=None)


class GoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = [
            "description",
            "name",
            "control_list_entries",
            "is_controlled",
            "part_number",
            "item_category",
            "is_pv_graded",
            "is_military_use",
            "is_component",
            "modified_military_use_details",
            "software_or_technology_details",
            "component_details",
            "uses_information_security",
            "information_security_details",
            "pv_grading",
        ]

    is_controlled = serializers.SerializerMethodField()
    control_list_entries = serializers.SerializerMethodField()
    is_military_use = serializers.SerializerMethodField()
    is_component = serializers.SerializerMethodField()
    item_category = serializers.SerializerMethodField()
    is_pv_graded = serializers.SerializerMethodField()
    pv_grading = serializers.SerializerMethodField()
    uses_information_security = FriendlyBooleanField()

    def get_pv_grading(self, obj):
        return PvGradingDetailsSerializer(obj.pv_grading_details).data

    def get_is_pv_graded(self, obj):
        return GoodPvGraded.to_str(obj.is_pv_graded)

    def get_item_category(self, obj):
        return ItemCategory.to_str(obj.item_category)

    def get_is_controlled(self, obj):
        return GoodControlled.to_str(obj.is_good_controlled)

    def get_is_military_use(self, obj):
        return MilitaryUse.to_str(obj.is_military_use)

    def get_is_component(self, obj):
        return Component.to_str(obj.is_component)

    def get_control_list_entries(self, obj):
        return [clc.rating for clc in obj.control_list_entries.all()]


class GoodOnApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodOnApplication
        fields = [
            "id",
            "good",
            "is_incorporated",
            "item_type",
            "other_item_type",
            "firearm_details",
            "applied_for_quantity",
            "applied_for_value",
            "created_at",
            "control_list_entries",
        ]

    good = GoodSerializer()
    firearm_details = FirearmDetailsSerializer()
    is_incorporated = FriendlyBooleanField(source="is_good_incorporated")
    applied_for_quantity = serializers.SerializerMethodField()
    applied_for_value = serializers.SerializerMethodField()
    control_list_entries = serializers.SerializerMethodField()

    def get_applied_for_quantity(self, obj):
        if hasattr(obj, "quantity"):
            return format_quantity(obj.quantity, obj.unit)
        return ""

    def get_applied_for_value(self, obj):
        if hasattr(obj, "value"):
            return f"£{obj.value}"
        return ""

    def get_control_list_entries(self, obj):
        return [clc.rating for clc in obj.control_list_entries.all()]


class GoodsQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsQuery
        fields = [
            "control_list_entry",
            "clc_raised_reasons",
            "pv_grading_raised_reasons",
            "good",
            "clc_responded",
            "pv_grading_responded",
        ]

    control_list_entry = serializers.CharField(source="clc_control_list_entry")
    clc_responded = FriendlyBooleanField()
    pv_grading_responded = FriendlyBooleanField()
    good = GoodsQueryGoodSerializer()


class CompliancePersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompliancePerson
        fields = ["name", "job_title"]


class ComplianceVisitCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceVisitCase
        fields = [
            "reference_code",
            "visit_type",
            "visit_date",
            "overall_risk_value",
            "licence_risk_value",
            "overview",
            "inspection",
            "compliance_overview",
            "compliance_risk_value",
            "individuals_overview",
            "individuals_risk_value",
            "products_overview",
            "products_risk_value",
            "people_present",
            "site_case",
        ]

    visit_type = serializers.SerializerMethodField()
    overall_risk_value = serializers.SerializerMethodField()
    compliance_risk_value = serializers.SerializerMethodField()
    individuals_risk_value = serializers.SerializerMethodField()
    products_risk_value = serializers.SerializerMethodField()
    visit_date = serializers.DateField(format=DATE_FORMAT, input_formats=None)
    people_present = serializers.SerializerMethodField()
    site_case = serializers.SerializerMethodField()

    def get_site_case(self, obj):
        return FlattenedComplianceSiteSerializer(obj.site_case).data

    def get_visit_type(self, obj):
        return ComplianceVisitTypes.to_str(obj.visit_type) if obj.visit_type else None

    def get_overall_risk_value(self, obj):
        return ComplianceRiskValues.to_str(obj.overall_risk_value) if obj.overall_risk_value else None

    def get_compliance_risk_value(self, obj):
        return ComplianceRiskValues.to_str(obj.compliance_risk_value) if obj.overall_risk_value else None

    def get_individuals_risk_value(self, obj):
        return ComplianceRiskValues.to_str(obj.individuals_risk_value) if obj.overall_risk_value else None

    def get_products_risk_value(self, obj):
        return ComplianceRiskValues.to_str(obj.products_risk_value) if obj.overall_risk_value else None

    def get_people_present(self, obj):
        people = CompliancePerson.objects.filter(visit_case=obj.id)
        return CompliancePersonSerializer(people, many=True)


class ComplianceVisitSerializer(ComplianceVisitCaseSerializer):
    def to_representation(self, obj):
        ret = super().to_representation(obj)
        comp_case = ComplianceVisitCase.objects.select_related("site_case").get(id=obj.id)
        ret = {**ret, **ComplianceVisitCaseSerializer(comp_case).data}
        return ret


class ComplianceSiteCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceVisitCase
        fields = ["reference_code", "address"]

    site_name = serializers.SerializerMethodField()
    address = AddressSerializer()
    licences = serializers.SerializerMethodField()

    def get_site_name(self, obj):
        return obj.compliancesitecase.site.name

    def to_representation(self, obj):
        ret = super().to_representation(obj)
        ret = {**ret, **ret["address"]}
        del ret["address"]
        return ret


class F680Serializer(serializers.ModelSerializer):

    application = serializers.SerializerMethodField()
    security_release_outcomes = serializers.SerializerMethodField()
    case_officer = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = ["application", "security_release_outcomes", "case_officer"]

    def get_application(self, obj):
        # Expose the application JSON to the template
        return obj.get_application().application

    def get_security_release_outcomes(self, obj):
        data = {}
        for outcome, _ in SecurityReleaseOutcomes.choices:
            sros = SecurityReleaseOutcome.objects.filter(case=obj, outcome=outcome)
            data[outcome] = SecurityReleaseOutcomeLetterSerializer(sros, many=True).data
        return data

    def get_case_officer(self, obj):
        case_officer = None
        qs = obj.case_assignments.filter(queue_id=QueuesEnum.MOD_ECJU_F680_CASES_UNDER_FINAL_REVIEW)
        if qs.exists():
            case_officer = qs.first().user

        return case_officer


class ComplianceSiteLicenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["reference_code", "status"]

    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        # The latest non draft licence should be the only active licence on a case or the licence that was active
        last_licence = (
            Licence.objects.filter(case_id=obj.id).exclude(status=LicenceStatus.DRAFT).order_by("created_at").last()
        )

        # not all obj types contain a licence, for example OGLs do not. As a result we display the case status
        if last_licence:
            return LicenceStatus.to_str(last_licence.status)
        else:
            return get_status_value_from_case_status_enum(obj.status.status)


class ComplianceSiteSerializer(serializers.Serializer):
    """
    Serializes a Case object
    """

    reference_code = serializers.CharField()
    site_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    licences = serializers.SerializerMethodField()

    def get_site_name(self, obj):
        return obj.compliancesitecase.site.name

    def get_address(self, obj):
        return AddressSerializer(obj.compliancesitecase.site.address).data

    def get_licences(self, obj):
        cases = Case.objects.filter_for_cases_related_to_compliance_case(obj.id)
        return ComplianceSiteLicenceSerializer(cases, many=True).data


class ComplianceSiteWithVisitReportsSerializer(ComplianceSiteSerializer):
    visit_reports = serializers.SerializerMethodField()

    def get_visit_reports(self, obj):
        visits = ComplianceVisitCase.objects.filter(site_case_id=obj.id)
        return ComplianceVisitCaseSerializer(visits, many=True).data


class FlattenedComplianceSiteSerializer(ComplianceSiteSerializer):
    def to_representation(self, obj):
        ret = super().to_representation(obj)
        ret = {**ret, **ret["address"]}
        del ret["address"]
        return ret


class FlattenedComplianceSiteWithVisitReportsSerializer(ComplianceSiteWithVisitReportsSerializer):
    def to_representation(self, obj):
        ret = super().to_representation(obj)
        ret = {**ret, **ret["address"]}
        del ret["address"]
        return ret


class AdviceSerializer(serializers.ModelSerializer):
    denial_reasons = DenialReasonSerializer(read_only=True, many=True)

    class Meta:
        model = Advice
        fields = ("type", "text", "note", "proviso", "denial_reasons")


def get_document_context(case, addressee=None):
    """
    Generate universal context dictionary to provide data for all document types.
    """
    date, time = get_date_and_time()
    licence = Licence.objects.get_draft_or_active_licence(case.pk)
    final_advice = Advice.objects.filter(level=AdviceLevel.FINAL, case_id=case.pk)
    ecju_queries = EcjuQuery.objects.filter(case=case)
    notes = CaseNote.objects.filter(case=case)
    sites = Site.objects.filter(sites_on_application__application_id=case.pk)
    external_locations = ExternalLocation.objects.filter(external_locations_on_application__application_id=case.pk)
    documents = ApplicationDocument.objects.filter(application_id=case.pk).order_by("-created_at")
    base_application = case.baseapplication if getattr(case, "baseapplication", "") else None
    if base_application:
        ultimate_end_users = (
            [p.party for p in base_application.ultimate_end_users] if base_application.ultimate_end_users else None
        )
    else:
        ultimate_end_users = None

    if getattr(base_application, "goods", "") and base_application.goods.exists():
        goods = _get_goods_context(base_application, final_advice, licence)
    else:
        goods = None

    # compliance type cases contain neither an addressee or submitted_by user
    if not addressee and case.submitted_by:
        addressee = case.submitted_by

    appeal_deadline = timezone.localtime() + timedelta(days=APPEAL_DAYS)
    exporter_reference = ""
    date_application_submitted = ""

    if base_application:
        if base_application.name:
            exporter_reference = base_application.name

        if base_application.submitted_at:
            date_application_submitted = base_application.submitted_at.strftime("%d %B %Y")

    return {
        "case_reference": case.reference_code,
        "case_submitted_at": case.submitted_at,
        "case_officer_name": case.get_case_officer_name(),
        "case_type": CaseTypeSerializer(case.case_type).data,
        "current_date": date,
        "current_time": time,
        "details": _get_details_context(case),
        "addressee": AddresseeSerializer(addressee).data,
        "organisation": OrganisationSerializer(case.organisation).data,
        "licence": LicenceSerializer(licence).data if licence else None,
        "end_user": (
            PartySerializer(base_application.end_user.party).data
            if base_application and base_application.end_user
            else None
        ),
        "consignee": (
            PartySerializer(base_application.consignee.party).data
            if base_application and base_application.consignee
            else None
        ),
        "ultimate_end_users": PartySerializer(ultimate_end_users, many=True).data or [],
        "third_parties": (
            _get_third_parties_context(base_application.third_parties)
            if getattr(base_application, "third_parties", "")
            else []
        ),
        "goods": goods,
        "ecju_queries": EcjuQuerySerializer(ecju_queries, many=True).data,
        "notes": CaseNoteSerializer(notes, many=True).data,
        "sites": FlattenedSiteSerializer(sites, many=True).data,
        "external_locations": ExternalLocationSerializer(external_locations, many=True).data,
        "documents": ApplicationDocumentSerializer(documents, many=True).data,
        "appeal_deadline": appeal_deadline.strftime("%d %B %Y"),
        "date_application_submitted": date_application_submitted,
        "exporter_reference": exporter_reference,
    }


# TODO: This mapping/serializers business feels nuts - we should just generate a context
#   dict in a function instead
SERIALIZER_MAPPING = {
    CaseTypeSubTypeEnum.STANDARD: FlattenedStandardApplicationSerializer,
    CaseTypeSubTypeEnum.EUA: EndUserAdvisoryQuerySerializer,
    CaseTypeSubTypeEnum.GOODS: GoodsQuerySerializer,
    CaseTypeSubTypeEnum.COMP_SITE: FlattenedComplianceSiteWithVisitReportsSerializer,
    CaseTypeSubTypeEnum.EUA: EndUserAdvisoryQueryCaseSerializer,
    CaseTypeSubTypeEnum.COMP_VISIT: ComplianceVisitSerializer,
    CaseTypeSubTypeEnum.F680: F680Serializer,
}


def _get_details_context(case):
    case_sub_type = case.case_type.sub_type

    if case_sub_type and case_sub_type in SERIALIZER_MAPPING:
        serializer = SERIALIZER_MAPPING[case_sub_type]
        return serializer(case).data
    else:
        return None


def _get_third_parties_context(third_parties):
    parties = [third_party.party for third_party in third_parties]
    third_parties_context = {"all": PartySerializer(parties, many=True).data}

    # Split third parties into lists based on role
    for role, _ in PartyRole.choices:
        third_parties_of_type = third_parties.filter(party__role=role)
        if third_parties_of_type:
            filtered_parties = [third_party.party for third_party in third_parties_of_type]
            third_parties_context[role] = PartySerializer(filtered_parties, many=True).data

    return third_parties_context


def format_quantity(quantity, unit):
    if quantity and unit:
        return " ".join(
            [
                intcomma(quantity),
                pluralise_unit(Units.to_str(unit), quantity),
            ]
        )
    elif unit:
        return "0 " + pluralise_unit(Units.to_str(unit), quantity)


def _get_good_on_application_context_with_advice(good_on_application, advice):
    good_context = GoodOnApplicationSerializer(good_on_application).data

    if advice:
        advice = AdviceSerializer(advice).data
        good_context["reason"] = advice["text"]
        good_context["note"] = advice["note"]
        good_context["denial_reasons"] = advice["denial_reasons"]
        good_context["proviso_reason"] = advice["proviso"]

    return good_context


def _get_good_on_licence_context(good_on_licence):
    good_context = GoodOnApplicationSerializer(good_on_licence.good).data
    good_context["quantity"] = format_quantity(good_on_licence.quantity, good_on_licence.good.unit)
    good_context["value"] = f"£{good_on_licence.value}"

    return good_context


def _get_goods_context(application, final_advice, licence=None):
    """
    TODO: We should re-write this function to more clearly avoid all the pitfalls
    we have bolted on to it.

    What would probably be better would be to start from a context datastructure from all the GoodOnApplication
    objects that **we know** need to be present on the licence; e.g. application.goods.filter(is_good_controlled=True)

    From there, it would probably be clearer to go through each of the Advice records, GoodOnLicence records etc
    and hydrate those original GoodOnApplication objects.

    Right now, we do things a little backwards and add records to the context datastructure/grab/rewrite/overwrite them.
    That makes this quite hard to understand what is going on and very easy for bugs to manifest.
    """
    goods_on_application = application.goods.all().order_by("created_at")
    final_advice = final_advice.filter(good_id__isnull=False)
    goods_context = {advice_type: [] for advice_type, _ in AdviceType.choices}

    # Create a mapping to get from Good.id to corresponding GoodOnApplication records
    #  Note: we map to a list of GoodOnApplication records as there may be more than one
    #  GoodOnApplication per Good for this application
    good_ids_to_goods_on_application = defaultdict(lambda: [])
    for good_on_application in goods_on_application:
        good_ids_to_goods_on_application[good_on_application.good_id].append(good_on_application)
    goods_context["all"] = GoodOnApplicationSerializer(goods_on_application, many=True).data

    if licence:
        goods_on_licence = licence.goods.all().order_by("created_at")
        if goods_on_licence.exists():
            goods_context[AdviceType.APPROVE] = [
                _get_good_on_licence_context(good_on_licence) for good_on_licence in goods_on_licence
            ]
        # Remove APPROVE from advice as it is no longer needed
        # (no need to get approved GoodOnApplications if we have GoodOnLicence)
        final_advice = final_advice.exclude(type=AdviceType.APPROVE)

    # Ensure that for each proviso final advice record, we add a record to the goods
    #  context
    for advice in final_advice:
        # Ignore final advice records where we have no associated good on application
        # - either our mapping value is missing or is an empty list so skip it.
        if not good_ids_to_goods_on_application.get(advice.good_id):
            continue
        # Grab the next GoodOnApplication for this Good.id - this ensures that
        #  each GoodOnApplication is present once on the end licence
        good_on_application = good_ids_to_goods_on_application[advice.good_id].pop(0)
        goods_context[advice.type].append(_get_good_on_application_context_with_advice(good_on_application, advice))

    # Because we append goods that are approved with proviso to the approved goods below
    # we need to make sure only to keep approved goods that are not in proviso goods
    # otherwise goods are duplicated in the licence document. Also we need to copy quantity
    # and value data from the approve good object to the proviso good object.
    if goods_context[AdviceType.PROVISO] != []:
        approve_goods = goods_context[AdviceType.APPROVE]
        proviso_goods = goods_context[AdviceType.PROVISO]
        # Copy quantity and value data from approve good to proviso good
        for proviso_good in proviso_goods:
            corresponding_approve_good = next(
                (x for x in approve_goods if x["id"] == proviso_good["id"]), None
            )  # get the corresponding approve good or None
            if corresponding_approve_good is not None:
                proviso_good.update(quantity=corresponding_approve_good["quantity"])
                proviso_good.update(value=corresponding_approve_good["value"])
        # Prevent against duplicate goods when proviso goods are moved into approved goods later
        approve_goods = [item for item in approve_goods if item["id"] not in [item["id"] for item in proviso_goods]]
        # Save into goods_context
        goods_context[AdviceType.APPROVE] = approve_goods
        goods_context[AdviceType.PROVISO] = proviso_goods

    # Move proviso elements into approved because they are treated the same
    goods_context[AdviceType.APPROVE].extend(goods_context.pop(AdviceType.PROVISO))
    # order them back in the original order
    approved_goods = goods_context.pop(AdviceType.APPROVE)
    ordered_goods = sorted(approved_goods, key=lambda d: d["created_at"])
    goods_context[AdviceType.APPROVE] = ordered_goods
    return goods_context
