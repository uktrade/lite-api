from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Q

from rest_framework import serializers

from api.applications.enums import GoodsTypeCategory, MTCRAnswers, ServiceEquipmentType
from api.cases.enums import AdviceLevel, AdviceType, CaseTypeSubTypeEnum, ECJUQueryType
from api.compliance.enums import ComplianceVisitTypes, ComplianceRiskValues
from api.licences.enums import LicenceStatus
from api.parties.enums import PartyRole, PartyType, SubType
from api.staticdata.f680_clearance_types.enums import F680ClearanceTypeEnum
from api.staticdata.units.enums import Units
from api.goods.enums import (
    PvGrading,
    ItemCategory,
    Component,
    MilitaryUse,
    FirearmGoodType,
    GoodControlled,
    GoodPvGraded,
)

from api.applications.models import (
    BaseApplication,
    ApplicationDocument,
    StandardApplication,
    OpenApplication,
    ExhibitionClearanceApplication,
    F680ClearanceApplication,
    HmrcQuery,
    CountryOnApplication,
    GoodOnApplication,
)
from api.goods.models import PvGradingDetails, Good, FirearmGoodDetails
from api.goodstype.models import GoodsType
from api.cases.models import Advice, EcjuQuery, CaseNote, Case, GoodCountryDecision, CaseType
from api.organisations.models import Organisation
from api.addresses.models import Address
from api.parties.models import Party
from api.compliance.models import ComplianceVisitCase, CompliancePerson, OpenLicenceReturns
from api.licences.models import Licence
from api.organisations.models import Site, ExternalLocation
from api.queries.end_user_advisories.models import EndUserAdvisoryQuery
from api.queries.goods_query.models import GoodsQuery

from api.staticdata.countries.models import Country

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


class FlattenedAddressSerializerMixin:
    def to_representation(self, obj):
        ret = super().to_representation(obj)
        ret = {**ret, **ret["address"]}
        del ret["address"]
        return ret


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


class FlattenedSiteSerializer(SiteSerializer, FlattenedAddressSerializerMixin):
    pass


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ["name", "eori_number", "sic_number", "vat_number", "registration_number", "primary_site"]

    primary_site = FlattenedSiteSerializer()


class LicenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licence
        fields = ["duration", "start_date", "end_date"]

    start_date = serializers.DateField(format=DATE_FORMAT, input_formats=None)
    end_date = serializers.SerializerMethodField()

    def get_end_date(self, obj):
        return add_months(obj.start_date, obj.duration)


class OpenLicenceReturnsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenLicenceReturns
        fields = ["file_name", "year", "timestamp"]

    file_name = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()

    def get_file_name(self, obj):
        return f"{obj.year}OpenLicenceReturns.csv"

    def get_timestamp(self, obj):
        return obj.created_at.strftime(f"{DATE_FORMAT} {TIME_FORMAT}")


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


class CountryOnApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountryOnApplication
        fields = ["country", "contract_types", "other_contract_type"]

    country = CountrySerializer()
    other_contract_type = serializers.SerializerMethodField()

    def get_other_contract_type(self, obj):
        return obj.other_contract_type_text


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
        return f"{obj.responded_by_user.first_name} {obj.responded_by_user.last_name}"


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


class F680ClearanceApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = F680ClearanceApplication
        fields = [
            "expedited",
            "expedited_date",
            "foreign_technology",
            "foreign_technology_description",
            "locally_manufactured",
            "locally_manufactured_description",
            "mtcr_type",
            "electronic_warfare_requirement",
            "uk_service_equipment",
            "uk_service_equipment_description",
            "uk_service_equipment_type",
            "prospect_value",
            "clearance_level",
            "clearance_types",
        ]

    expedited_date = serializers.DateField(format=DATE_FORMAT, input_formats=None)
    expedited = FriendlyBooleanField()
    foreign_technology = FriendlyBooleanField()
    locally_manufactured = FriendlyBooleanField()
    electronic_warfare_requirement = FriendlyBooleanField()
    uk_service_equipment = FriendlyBooleanField()
    clearance_types = serializers.SerializerMethodField()
    mtcr_type = serializers.SerializerMethodField()
    uk_service_equipment_type = serializers.SerializerMethodField()
    clearance_level = serializers.SerializerMethodField()

    def get_uk_service_equipment_type(self, obj):
        return ServiceEquipmentType.to_str(obj.uk_service_equipment_type) if obj.uk_service_equipment_type else None

    def get_mtcr_type(self, obj):
        return MTCRAnswers.to_str(obj.mtcr_type) if obj.mtcr_type else None

    def get_clearance_types(self, obj):
        return [F680ClearanceTypeEnum.get_text(f680_type.name) for f680_type in obj.types.all()]

    def get_clearance_level(self, obj):
        return PvGrading.to_str(obj.clearance_level)


class FlattenedF680ClearanceApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["baseapplication"]

    baseapplication = BaseApplicationSerializer()

    def to_representation(self, obj):
        ret = super().to_representation(obj)
        f680 = F680ClearanceApplication.objects.get(id=obj.pk)
        f680_data = F680ClearanceApplicationSerializer(f680).data
        serialized = {**ret["baseapplication"], **f680_data}
        return serialized


class TemporaryExportDetailsSerializer(serializers.Serializer):
    """
        Serializes both OpenApplication and StandardApplication
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


class OpenApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenApplication
        fields = [
            "export_type",
            "contains_firearm_goods",
            "shipped_waybill_or_lading",
            "non_waybill_or_lading_route_details",
            "proposed_return_date",
            "trade_control_activity",
            "trade_control_activity_other",
            "trade_control_product_categories",
            "goodstype_category",
            "temporary_export_details",
        ]

    contains_firearm_goods = FriendlyBooleanField()
    shipped_waybill_or_lading = FriendlyBooleanField(source="is_shipped_waybill_or_lading")
    proposed_return_date = serializers.DateField(format=DATE_FORMAT, input_formats=None)
    goodstype_category = serializers.SerializerMethodField()
    temporary_export_details = serializers.SerializerMethodField()

    def get_temporary_export_details(self, obj):
        return TemporaryExportDetailsSerializer(obj).data

    def get_goodstype_category(self, obj):
        return GoodsTypeCategory.get_text(obj.goodstype_category) if obj.goodstype_category else None


class FlattenedOpenApplicationSerializer(OpenApplicationSerializer):
    class Meta:
        model = Case
        fields = ["baseapplication"]

    baseapplication = BaseApplicationSerializer()

    def to_representation(self, obj):
        ret = super().to_representation(obj)
        open_application = OpenApplication.objects.get(id=obj.pk)
        open_application_data = OpenApplicationSerializer(open_application).data
        serialized = {**ret["baseapplication"], **open_application_data}
        return serialized


class ExhibitionClearanceApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExhibitionClearanceApplication
        fields = ["exhibition_title", "first_exhibition_date", "required_by_date", "reason_for_clearance"]

    exhibition_title = serializers.CharField()
    first_exhibition_date = serializers.DateField(format=DATE_FORMAT, input_formats=None)
    required_by_date = serializers.DateField(format=DATE_FORMAT, input_formats=None)


class FlattenedExhibitionClearanceApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["baseapplication"]

    baseapplication = BaseApplicationSerializer()

    def to_representation(self, obj):
        ret = super().to_representation(obj)
        exhibition_clearance = ExhibitionClearanceApplication.objects.get(id=obj.pk)
        exhibition_clearance_data = ExhibitionClearanceApplicationSerializer(exhibition_clearance).data
        serialized = {**ret["baseapplication"], **exhibition_clearance_data}
        return serialized


class HmrcQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = HmrcQuery
        fields = ["query_reason", "have_goods_departed"]

    query_reason = serializers.CharField(source="reasoning")
    have_goods_departed = FriendlyBooleanField()


class FlattenedHmrcQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["baseapplication"]

    baseapplication = BaseApplicationSerializer()

    def to_representation(self, obj):
        ret = super().to_representation(obj)
        hmrc_query = HmrcQuery.objects.get(id=obj.pk)
        hmrc_query_data = HmrcQuerySerializer(hmrc_query).data
        serialized = {**ret["baseapplication"], **hmrc_query_data}
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


class GoodsTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsType
        fields = ["description", "control_list_entries", "is_controlled"]

    control_list_entries = serializers.SerializerMethodField()
    is_controlled = FriendlyBooleanField(source="is_good_controlled")

    def get_control_list_entries(self, obj):
        return [clc.rating for clc in obj.control_list_entries.all()]


class GoodsQueryGoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = ["description", "name", "control_list_entries", "is_controlled", "part_number"]

    is_controlled = serializers.NullBooleanField(source="is_good_controlled")
    control_list_entries = serializers.SerializerMethodField()

    def get_control_list_entries(self, obj):
        return [clc.rating for clc in obj.control_list_entries.all()]


class FlattenedGoodMixin:
    def to_representation(self, obj):
        ret = super().to_representation(obj)
        ret = {**ret, **ret["good"]}
        del ret["good"]
        return ret


class FirearmsDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirearmGoodDetails
        fields = [
            "firearm_type",
            "year_of_manufacture",
            "calibre",
            "is_covered_by_firearm_act_section_one_two_or_five",
            "section_certificate_number",
            "section_certificate_date_of_expiry",
            "has_identification_markings",
            "identification_markings_details",
            "no_identification_markings_details",
        ]

    firearm_type = serializers.SerializerMethodField()
    is_covered_by_firearm_act_section_one_two_or_five = FriendlyBooleanField()

    def get_firearm_type(self, obj):
        return FirearmGoodType.to_str(obj.type)


class GoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = [
            "description",
            "name",
            "control_list_entries",
            "is_controlled",
            "part_number",
            "applied_for_quantity",
            "applied_for_value",
            "item_category",
            "is_pv_graded",
            "is_military_use",
            "is_component",
            "modified_military_use_details",
            "component_details",
            "uses_information_security",
            "information_security_details",
        ]

    is_controlled = serializers.SerializerMethodField()
    control_list_entries = serializers.SerializerMethodField()
    applied_for_quantity = serializers.SerializerMethodField()
    applied_for_value = serializers.SerializerMethodField()
    is_military_use = serializers.SerializerMethodField()
    is_component = serializers.SerializerMethodField()
    uses_information_security = FriendlyBooleanField()

    def get_is_controlled(self, obj):
        return GoodControlled.to_str(obj.is_good_controlled)

    def get_is_military_use(self, obj):
        return MilitaryUse.to_str(obj.is_military_use)

    def get_is_component(self, obj):
        return Component.to_str(obj.is_component)

    def get_control_list_entries(self, obj):
        return [clc.rating for clc in obj.control_list_entries.all()]

    def get_applied_for_quantity(self, obj):
        if hasattr(obj, "quantity"):
            return format_quantity(obj.quantity, obj.unit)
        return None

    def get_applied_for_value(self, obj):
        if hasattr(obj, "value"):
            return f"£{obj.value}"
        return None


class GoodOnApplicationSerializer(serializers.ModelSerializer, FlattenedGoodMixin):
    class Meta:
        model = GoodOnApplication
        fields = ["good", "is_incorporated", "item_type", "other_item_type", "firearm_details"]

    good = GoodSerializer()
    firearm_details = serializers.SerializerMethodField()
    is_incorporated = FriendlyBooleanField(source="is_good_incorporated")

    def get_firearm_details(self, obj):
        return obj.firearm_details or obj.good.firearm_details


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


class ComplianceSiteCaseSerializer(serializers.ModelSerializer, FlattenedAddressSerializerMixin):
    class Meta:
        model = ComplianceVisitCase
        fields = ["reference_code", "address"]

    site_name = serializers.SerializerMethodField()
    address = AddressSerializer()
    open_licence_returns = serializers.SerializerMethodField()
    licences = serializers.SerializerMethodField()

    def get_site_name(self, obj):
        return obj.compliancesitecase.site.name


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


class ComplianceSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["reference_code", "site_name", "open_licence_returns", "licences"]

    site_name = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    open_licence_returns = serializers.SerializerMethodField()
    licences = serializers.SerializerMethodField()

    def get_site_name(self, obj):
        return obj.compliancesitecase.site.name

    def get_address(self, obj):
        return AddressSerializer(obj.compliancesitecase.site.address).data

    def get_open_licence_returns(self, obj):
        olrs = OpenLicenceReturns.objects.filter(organisation_id=obj.organisation.id).order_by("-year", "-created_at")
        return OpenLicenceReturnsSerializer(olrs, many=True).data

    def get_licences(self, obj):
        cases = Case.objects.filter_for_cases_related_to_compliance_case(obj.id)
        return ComplianceSiteLicenceSerializer(cases, many=True).data


class ComplianceSiteWithVisitReportsSerializer(ComplianceSiteSerializer):
    visit_reports = serializers.SerializerMethodField()

    def get_visit_reports(self, obj):
        visits = ComplianceVisitCase.objects.filter(site_case_id=obj.id)
        return ComplianceVisitCaseSerializer(visits, many=True).data


class FlattenedComplianceSiteSerializer(ComplianceSiteSerializer, FlattenedAddressSerializerMixin):
    pass


class FlattenedComplianceSiteWithVisitReportsSerializer(
    ComplianceSiteWithVisitReportsSerializer, FlattenedAddressSerializerMixin
):
    pass


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
    destinations = CountryOnApplication.objects.filter(application_id=case.pk).order_by("country__name")
    base_application = case.baseapplication if getattr(case, "baseapplication", "") else None
    if base_application:
        ultimate_end_users = (
            [p.party for p in base_application.ultimate_end_users] if base_application.ultimate_end_users else None
        )
    else:
        ultimate_end_users = None

    if getattr(base_application, "goods", "") and base_application.goods.exists():
        goods = _get_goods_context(base_application, final_advice, licence)
    elif getattr(base_application, "goods_type", "") and base_application.goods_type.exists():
        goods = _get_goods_type_context(
            base_application.goods_type.all()
            .order_by("created_at")
            .prefetch_related("countries", "control_list_entries"),
            case.pk,
        )
    else:
        goods = None

    # compliance type cases contain neither an addressee or submitted_by user
    if not addressee and case.submitted_by:
        addressee = case.submitted_by

    return {
        "case_reference": case.reference_code,
        "case_type": CaseTypeSerializer(case.case_type).data,
        "current_date": date,
        "current_time": time,
        "details": _get_details_context(case),
        "addressee": AddresseeSerializer(addressee).data,
        "organisation": OrganisationSerializer(case.organisation).data,
        "licence": LicenceSerializer(licence).data if licence else None,
        "end_user": PartySerializer(base_application.end_user.party).data if base_application and base_application.end_user else None,
        "consignee": PartySerializer(base_application.consignee.party).data if base_application and base_application.consignee else None,
        "ultimate_end_users": PartySerializer(ultimate_end_users, many=True).data or [],
        "third_parties": _get_third_parties_context(base_application.third_parties)
        if getattr(base_application, "third_parties", "")
        else [],
        "goods": goods,
        "ecju_queries": EcjuQuerySerializer(ecju_queries, many=True).data,
        "notes": CaseNoteSerializer(notes, many=True).data,
        "sites": FlattenedSiteSerializer(sites, many=True).data,
        "external_locations": ExternalLocationSerializer(external_locations, many=True).data,
        "documents": ApplicationDocumentSerializer(documents, many=True).data,
        "destinations": CountryOnApplicationSerializer(destinations, many=True).data,
    }


SERIALIZER_MAPPING = {
    CaseTypeSubTypeEnum.STANDARD: FlattenedStandardApplicationSerializer,
    CaseTypeSubTypeEnum.OPEN: FlattenedOpenApplicationSerializer,
    CaseTypeSubTypeEnum.HMRC: FlattenedHmrcQuerySerializer,
    CaseTypeSubTypeEnum.EXHIBITION: FlattenedExhibitionClearanceApplicationSerializer,
    CaseTypeSubTypeEnum.F680: FlattenedF680ClearanceApplicationSerializer,
    CaseTypeSubTypeEnum.GIFTING: BaseApplicationSerializer,
    CaseTypeSubTypeEnum.EUA: EndUserAdvisoryQuerySerializer,
    CaseTypeSubTypeEnum.GOODS: GoodsQuerySerializer,
    CaseTypeSubTypeEnum.COMP_SITE: FlattenedComplianceSiteWithVisitReportsSerializer,
    CaseTypeSubTypeEnum.EUA: EndUserAdvisoryQueryCaseSerializer,
    CaseTypeSubTypeEnum.COMP_VISIT: ComplianceVisitSerializer,
}


def _get_details_context(case):
    case_sub_type = case.case_type.sub_type

    if case_sub_type and case_sub_type in SERIALIZER_MAPPING:
        serializer = SERIALIZER_MAPPING[case_sub_type]
        if serializer == FlattenedComplianceSiteWithVisitReportsSerializer:
            import pdb; pdb.set_trace()
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
        return " ".join([intcomma(quantity), pluralise_unit(Units.to_str(unit), quantity),])
    elif unit:
        return "0 " + pluralise_unit(Units.to_str(unit), quantity)


def _get_good_on_application_context(good_on_application, advice=None):

    good_context = GoodOnApplicationSerializer(good_on_application).data

    # handle item categories for goods and their differences
    if good_on_application.good.item_category in ItemCategory.group_two:
        firearm_details = good_on_application.firearm_details or good_on_application.good.firearm_details
        good_context["firearm_type"] = FirearmGoodType.to_str(firearm_details.type)
        good_context["year_of_manufacture"] = firearm_details.year_of_manufacture
        good_context["calibre"] = firearm_details.calibre
        good_context["is_covered_by_firearm_act_section_one_two_or_five"] = friendly_boolean(
            firearm_details.is_covered_by_firearm_act_section_one_two_or_five
        )

        if firearm_details.is_covered_by_firearm_act_section_one_two_or_five:
            good_context["section_certificate_number"] = firearm_details.section_certificate_number
            good_context["section_certificate_date_of_expiry"] = firearm_details.section_certificate_date_of_expiry

        good_context["has_identification_markings"] = friendly_boolean(firearm_details.has_identification_markings)

        if firearm_details.has_identification_markings:
            good_context["identification_markings_details"] = firearm_details.identification_markings_details

        else:
            good_context["no_identification_markings_details"] = firearm_details.no_identification_markings_details

    elif good_on_application.good.item_category in ItemCategory.group_three:
        good_context["is_military_use"] = MilitaryUse.to_str(good_on_application.good.is_military_use)

        if good_on_application.good.is_military_use == MilitaryUse.YES_MODIFIED:
            good_context["modified_military_use_details"] = good_on_application.good.modified_military_use_details

        good_context["software_or_technology_details"] = good_on_application.good.software_or_technology_details
        good_context["uses_information_security"] = friendly_boolean(good_on_application.good.uses_information_security)

        if good_on_application.good.uses_information_security:
            good_context["information_security_details"] = good_on_application.good.information_security_details

    if advice:
        good_context["reason"] = advice.text
        good_context["note"] = advice.note

        if advice.proviso:
            good_context["proviso_reason"] = advice.proviso

    if good_on_application.good.is_pv_graded != GoodPvGraded.NO:
        good_context["pv_grading"] = PvGradingDetailsSerializer(good_on_application.good.pv_grading_details).data

    return good_context


def _get_good_on_licence_context(good_on_licence, advice=None):
    good_context = _get_good_on_application_context(good_on_licence.good, advice)
    good_context["quantity"] = format_quantity(good_on_licence.quantity, good_on_licence.good.unit)
    good_context["value"] = f"£{good_on_licence.value}"

    return good_context


def _get_goods_context(application, final_advice, licence=None):
    goods_on_application = application.goods.all().order_by("good__description")
    final_advice = final_advice.filter(good_id__isnull=False)
    goods_context = {advice_type: [] for advice_type, _ in AdviceType.choices}

    goods_on_application_dict = {
        good_on_application.good_id: good_on_application for good_on_application in goods_on_application
    }
    goods_context["all"] = [_get_good_on_application_context(good) for good in goods_on_application]

    if licence:
        goods_on_licence = licence.goods.all().order_by("good__good__description")
        if goods_on_licence.exists():
            goods_context[AdviceType.APPROVE] = [
                _get_good_on_licence_context(good_on_licence) for good_on_licence in goods_on_licence
            ]
        # Remove APPROVE from advice as it is no longer needed
        # (no need to get approved GoodOnApplications if we have GoodOnLicence)
        final_advice = final_advice.exclude(type=AdviceType.APPROVE)

    for advice in final_advice:
        good_on_application = goods_on_application_dict[advice.good_id]
        goods_context[advice.type].append(_get_good_on_application_context(good_on_application, advice))

    # Move proviso elements into approved because they are treated the same
    goods_context[AdviceType.APPROVE].extend(goods_context.pop(AdviceType.PROVISO))
    return goods_context


def _get_approved_goods_type_context(approved_goods_type_on_country_decisions):
    # Approved goods types on country
    if approved_goods_type_on_country_decisions:
        context = {}
        for decision in approved_goods_type_on_country_decisions:
            if decision.country.name not in context:
                context[decision.country.name] = [GoodsTypeSerializer(decision.goods_type).data]
            else:
                context[decision.country.name].append(GoodsTypeSerializer(decision.goods_type).data)
        return context


def _get_entities_refused_at_the_final_advice_level(case_pk):
    # Get Refused Final advice on Country & GoodsType
    rejected_entities = Advice.objects.filter(
        Q(goods_type__isnull=False) | Q(country__isnull=False),
        case_id=case_pk,
        level=AdviceLevel.FINAL,
        type=AdviceType.REFUSE,
    ).prefetch_related("goods_type", "goods_type__control_list_entries", "country")

    refused_final_advice_countries = []
    refused_final_advice_goods_types = []
    for rejected_entity in rejected_entities:
        if rejected_entity.goods_type:
            refused_final_advice_goods_types.append(rejected_entity.goods_type)
        else:
            refused_final_advice_countries.append(rejected_entity.country)

    return refused_final_advice_countries, refused_final_advice_goods_types


def _get_refused_goods_type_context(case_pk, goods_types, refused_goods_type_on_country_decisions):
    # Refused goods types on country from GoodCountryDecisions
    context = {}
    if refused_goods_type_on_country_decisions:
        for decision in refused_goods_type_on_country_decisions:
            if decision.country.name not in context:
                context[decision.country.name] = {decision.goods_type.id: GoodsTypeSerializer(decision.goods_type).data}
            else:
                context[decision.country.name][decision.goods_type.id] = GoodsTypeSerializer(decision.goods_type).data

    refused_final_advice_countries, refused_final_advice_goods_types = _get_entities_refused_at_the_final_advice_level(
        case_pk
    )

    # Countries refused for all goods types at final advice level
    if refused_final_advice_countries:
        for country in refused_final_advice_countries:
            goods_type_for_country = goods_types.filter(countries=country)
            for goods_type in goods_type_for_country:
                if country.name not in context:
                    context[country.name] = {goods_type.id: GoodsTypeSerializer(goods_type).data}
                elif goods_type.id not in context[country.name]:
                    context[country.name][goods_type.id] = GoodsTypeSerializer(goods_type).data

    # Goods types refused for all countries at final advice level
    if refused_final_advice_goods_types:
        for goods_type in refused_final_advice_goods_types:
            for country in goods_type.countries.all():
                if country.name not in context:
                    context[country.name] = {goods_type.id: GoodsTypeSerializer(goods_type).data}
                elif goods_type.id not in context[country.name]:
                    context[country.name][goods_type.id] = GoodsTypeSerializer(goods_type).data

    # Remove ID's used to avoid duplication
    return {key: list(context[key].values()) for key in context} if context else None


def _get_goods_type_context(goods_types, case_pk):
    goods_type_context = {"all": [GoodsTypeSerializer(goods_type).data for goods_type in goods_types]}

    # Get GoodCountryDecisions
    goods_type_on_country_decisions = GoodCountryDecision.objects.filter(case_id=case_pk).prefetch_related(
        "goods_type", "goods_type__control_list_entries", "country"
    )
    approved_goods_type_on_country_decisions = []
    refused_goods_type_on_country_decisions = []
    for goods_type_on_country_decision in goods_type_on_country_decisions:
        if goods_type_on_country_decision.approve:
            approved_goods_type_on_country_decisions.append(goods_type_on_country_decision)
        else:
            refused_goods_type_on_country_decisions.append(goods_type_on_country_decision)

    approved_goods_type_context = _get_approved_goods_type_context(approved_goods_type_on_country_decisions)
    if approved_goods_type_context:
        goods_type_context[AdviceType.APPROVE] = approved_goods_type_context

    refused_goods_type_context = _get_refused_goods_type_context(
        case_pk, goods_types, refused_goods_type_on_country_decisions
    )
    if refused_goods_type_context:
        goods_type_context[AdviceType.REFUSE] = refused_goods_type_context

    return goods_type_context
