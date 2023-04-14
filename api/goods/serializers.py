from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from api.core.helpers import str_to_bool
from api.core.serializers import KeyValueChoiceField, ControlListEntryField, GoodControlReviewSerializer
from api.documents.libraries.process_document import process_document
from api.goods.enums import (
    FirearmCategory,
    GoodStatus,
    GoodControlled,
    GoodPvGraded,
    PvGrading,
    ItemCategory,
    MilitaryUse,
    Component,
    FirearmGoodType,
)
from api.applications.models import GoodOnApplication
from api.flags.enums import SystemFlags
from api.goods.helpers import (
    FIREARMS_CORE_TYPES,
    validate_firearms_act_certificate,
)
from api.goods.models import Good, GoodDocument, PvGradingDetails, FirearmGoodDetails, GoodControlListEntry
from api.gov_users.serializers import GovUserSimpleSerializer
from api.staticdata.report_summaries.models import ReportSummarySubject, ReportSummaryPrefix
from api.staticdata.report_summaries.serializers import ReportSummaryPrefixSerializer, ReportSummarySubjectSerializer
from lite_content.lite_api import strings
from api.organisations.models import Organisation
from api.queries.goods_query.models import GoodsQuery
from api.staticdata.control_list_entries.serializers import ControlListEntrySerializer
from api.staticdata.regimes.models import RegimeEntry
from api.staticdata.regimes.serializers import RegimeEntrySerializer
from api.staticdata.missing_document_reasons.enums import GoodMissingDocumentReasons
from api.staticdata.statuses.libraries.get_case_status import get_status_value_from_case_status_enum
from api.users.models import ExporterUser
from api.users.serializers import ExporterUserSimpleSerializer


class PvGradingDetailsSerializer(serializers.ModelSerializer):
    grading = KeyValueChoiceField(choices=PvGrading.choices + PvGrading.choices_new, allow_null=True, allow_blank=True)
    prefix = serializers.CharField(allow_blank=True, allow_null=True)
    suffix = serializers.CharField(allow_blank=True, allow_null=True)
    issuing_authority = serializers.CharField(allow_blank=False, allow_null=False)
    reference = serializers.CharField(allow_blank=False, allow_null=False)
    date_of_issue = serializers.DateField(
        allow_null=False,
        error_messages={"invalid": "Enter the product's date of issue and include a day, month, year."},
    )

    class Meta:
        model = PvGradingDetails
        fields = ("grading", "prefix", "suffix", "issuing_authority", "reference", "date_of_issue")


class FirearmDetailsSerializer(serializers.ModelSerializer):
    type = KeyValueChoiceField(
        choices=FirearmGoodType.choices,
        allow_null=False,
        error_messages={"null": strings.Goods.FIREARM_GOOD_NO_TYPE},
        required=False,
    )
    category = serializers.ListField(
        child=KeyValueChoiceField(
            choices=FirearmCategory.choices,
        ),
        allow_null=True,
        required=False,
    )
    is_made_before_1938 = serializers.BooleanField(allow_null=True, required=False)
    year_of_manufacture = serializers.IntegerField(
        allow_null=False,
        required=False,
        error_messages={
            "null": strings.Goods.FIREARM_GOOD_NO_YEAR_OF_MANUFACTURE,
            "invalid": strings.Goods.FIREARM_GOOD_YEAR_MUST_BE_VALID,
        },
    )
    calibre = serializers.CharField(
        allow_blank=True, required=False, error_messages={"null": strings.Goods.FIREARM_GOOD_NO_CALIBRE}
    )
    is_replica = serializers.BooleanField(allow_null=True, required=False)
    replica_description = serializers.CharField(allow_blank=True, required=False)
    # this refers specifically to section 1, 2 or 5 of firearms act 1968
    is_covered_by_firearm_act_section_one_two_or_five = serializers.CharField(allow_blank=True, required=False)
    is_covered_by_firearm_act_section_one_two_or_five_explanation = serializers.CharField(
        allow_blank=True, required=False
    )
    firearms_act_section = serializers.CharField(allow_blank=True, required=False)
    section_certificate_missing = serializers.BooleanField(allow_null=True, required=False)
    section_certificate_missing_reason = serializers.CharField(allow_blank=True, required=False)
    section_certificate_number = serializers.CharField(
        allow_blank=True, allow_null=True, required=False, max_length=100
    )
    section_certificate_date_of_expiry = serializers.DateField(
        allow_null=True, required=False, error_messages={"invalid": strings.Goods.FIREARM_GOOD_NO_EXPIRY_DATE}
    )
    no_identification_markings_details = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=2000
    )
    serial_numbers_available = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    is_deactivated = serializers.BooleanField(allow_null=True, required=False)
    date_of_deactivation = serializers.DateField(allow_null=True, required=False)
    deactivation_standard = serializers.CharField(allow_blank=True, required=False)
    deactivation_standard_other = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    number_of_items = serializers.IntegerField(
        allow_null=False,
        required=False,
        error_messages={"null": "Enter the number of items", "invalid": "Number of items must be valid"},
    )
    not_deactivated_to_standard_comments = serializers.CharField(allow_blank=True, required=False)
    serial_numbers = serializers.ListField(child=serializers.CharField(allow_blank=True), required=False)

    class Meta:
        model = FirearmGoodDetails
        fields = (
            "type",
            "category",
            "is_made_before_1938",
            "year_of_manufacture",
            "calibre",
            "is_replica",
            "replica_description",
            "is_covered_by_firearm_act_section_one_two_or_five",
            "is_covered_by_firearm_act_section_one_two_or_five_explanation",
            "firearms_act_section",
            "section_certificate_missing",
            "section_certificate_missing_reason",
            "section_certificate_number",
            "section_certificate_date_of_expiry",
            "no_identification_markings_details",
            "serial_numbers_available",
            "has_proof_mark",
            "no_proof_mark_details",
            "is_deactivated",
            "is_deactivated_to_standard",
            "date_of_deactivation",
            "deactivation_standard",
            "deactivation_standard_other",
            "number_of_items",
            "serial_numbers",
            "not_deactivated_to_standard_comments",
        )

    def validate(self, data):
        validated_data = super(FirearmDetailsSerializer, self).validate(data)

        if "section_certificate_number" in validated_data:
            validate_firearms_act_certificate(validated_data)

        return validated_data

    def update(self, instance, validated_data):
        instance.type = validated_data.get("type", instance.type)
        instance.category = validated_data.get("category", instance.category)
        instance.is_made_before_1938 = validated_data.get("is_made_before_1938", instance.is_made_before_1938)
        instance.year_of_manufacture = validated_data.get("year_of_manufacture", instance.year_of_manufacture)
        instance.calibre = validated_data.get("calibre", instance.calibre)

        instance.is_replica = validated_data.get("is_replica", instance.is_replica)
        instance.replica_description = (
            validated_data.get("replica_description", instance.replica_description) if instance.is_replica else ""
        )

        is_covered_by_firearms_act = validated_data.get(
            "is_covered_by_firearm_act_section_one_two_or_five",
            instance.is_covered_by_firearm_act_section_one_two_or_five,
        )
        instance.is_covered_by_firearm_act_section_one_two_or_five = is_covered_by_firearms_act
        is_covered_by_firearm_act_section_one_two_or_five_explanation = validated_data.get(
            "is_covered_by_firearm_act_section_one_two_or_five_explanation",
            instance.is_covered_by_firearm_act_section_one_two_or_five_explanation,
        )
        instance.is_covered_by_firearm_act_section_one_two_or_five_explanation = (
            is_covered_by_firearm_act_section_one_two_or_five_explanation
        )
        instance.firearms_act_section = validated_data.get("firearms_act_section", instance.firearms_act_section)

        if is_covered_by_firearms_act == "Yes" and instance.firearms_act_section:
            instance.section_certificate_number = validated_data.get(
                "section_certificate_number", instance.section_certificate_number
            )
            instance.section_certificate_date_of_expiry = validated_data.get(
                "section_certificate_date_of_expiry", instance.section_certificate_date_of_expiry
            )
            instance.section_certificate_missing = validated_data.get(
                "section_certificate_missing", instance.section_certificate_missing
            )
            instance.section_certificate_missing_reason = validated_data.get(
                "section_certificate_missing_reason", instance.section_certificate_missing_reason
            )
        else:
            instance.firearms_act_section = ""
            instance.section_certificate_number = ""
            instance.section_certificate_date_of_expiry = None
            instance.section_certificate_missing = False
            instance.section_certificate_missing_reason = ""

        certificate_missing = validated_data.get("section_certificate_missing", False) is True
        if certificate_missing:
            instance.section_certificate_number = ""
            instance.section_certificate_date_of_expiry = None
            instance.section_certificate_missing = True
            instance.section_certificate_missing_reason = validated_data.get(
                "section_certificate_missing_reason", instance.section_certificate_missing_reason
            )
        else:
            instance.section_certificate_missing = False
            instance.section_certificate_missing_reason = ""

        # Update just the certificate and expiryy date fields if changed
        instance.section_certificate_number = validated_data.get(
            "section_certificate_number", instance.section_certificate_number
        )
        instance.section_certificate_date_of_expiry = validated_data.get(
            "section_certificate_date_of_expiry", instance.section_certificate_date_of_expiry
        )

        instance.number_of_items = validated_data.get("number_of_items", instance.number_of_items)

        if "serial_numbers_available" in validated_data and validated_data.get("serial_numbers_available") is not None:
            instance.serial_numbers_available = validated_data.get("serial_numbers_available")
            if FirearmGoodDetails.SerialNumberAvailability.has_serial_numbers(instance.serial_numbers_available):
                instance.no_identification_marking_details = ""
            else:
                instance.no_identification_markings_details = validated_data.get(
                    "no_identification_markings_details", instance.no_identification_markings_details
                )

        instance.serial_numbers = validated_data.get("serial_numbers", instance.serial_numbers)

        if "is_deactivated" in validated_data:
            if validated_data["is_deactivated"]:
                instance.is_deactivated = validated_data["is_deactivated"]
                instance.date_of_deactivation = validated_data.get(
                    "date_of_deactivation",
                    instance.date_of_deactivation,
                )
                instance.is_deactivated_to_standard = validated_data.get(
                    "is_deactivated_to_standard",
                    instance.is_deactivated_to_standard,
                )
                instance.not_deactivated_to_standard_comments = validated_data.get(
                    "not_deactivated_to_standard_comments",
                    instance.not_deactivated_to_standard_comments,
                )
            else:
                instance.is_deactivated = validated_data["is_deactivated"]
                instance.date_of_deactivation = None
                instance.is_deactivated_to_standard = None
                instance.not_deactivated_to_standard_comments = ""

        if instance.type != "firearms":
            instance.is_replica = None
            instance.replica_description = ""

        if instance.type not in FIREARMS_CORE_TYPES:
            instance.is_covered_by_firearm_act_section_one_two_or_five = ""
            instance.is_covered_by_firearm_act_section_one_two_or_five_explanation = ""
            instance.serial_numbers_available = ""
            instance.year_of_manufacture = None
            instance.calibre = ""
            instance.section_certificate_number = ""
            instance.section_certificate_date_of_expiry = None
            instance.no_identification_markings_details = ""

        instance.save()
        return instance


class FirearmDetailsAttachingSerializer(serializers.Serializer):
    category = serializers.ListField(
        child=KeyValueChoiceField(
            choices=FirearmCategory.choices,
        ),
        allow_null=True,
        required=False,
    )
    section_certificate_missing = serializers.BooleanField(allow_null=True, required=False)
    section_certificate_missing_reason = serializers.CharField(allow_blank=True, required=False)
    section_certificate_number = serializers.CharField(
        allow_blank=True, allow_null=True, required=False, max_length=100
    )
    section_certificate_date_of_expiry = serializers.DateField(
        allow_null=True, required=False, error_messages={"invalid": strings.Goods.FIREARM_GOOD_NO_EXPIRY_DATE}
    )

    def update(self, instance, validated_data):
        for field_to_update in [
            "category",
            "section_certificate_missing",
            "section_certificate_missing_reason",
            "section_certificate_number",
            "section_certificate_date_of_expiry",
        ]:
            setattr(
                instance,
                field_to_update,
                validated_data.get(
                    field_to_update,
                    getattr(instance, field_to_update),
                ),
            )
        instance.save()
        return instance


class GoodListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    control_list_entries = ControlListEntrySerializer(many=True, allow_null=True)
    part_number = serializers.CharField()
    status = KeyValueChoiceField(choices=GoodStatus.choices)
    firearm_details = FirearmDetailsSerializer(read_only=True)
    item_category = KeyValueChoiceField(choices=ItemCategory.choices)


class GoodAttachingSerializer(serializers.ModelSerializer):
    firearm_details = FirearmDetailsAttachingSerializer(allow_null=True, required=False)

    class Meta:
        model = Good
        fields = ("firearm_details",)

    def update(self, instance, validated_data):
        if instance.item_category not in ItemCategory.group_two:
            return instance

        firearm_details = validated_data.get("firearm_details")
        if not firearm_details:
            return instance

        instance.firearm_details = self.update_firearm_details(
            instance=instance.firearm_details,
            firearm_details=firearm_details,
        )
        return instance

    def update_firearm_details(self, firearm_details, instance):
        serializer = FirearmDetailsAttachingSerializer()

        return serializer.update(
            instance=instance,
            validated_data=firearm_details,
        )


class GoodCreateSerializer(serializers.ModelSerializer):
    """
    This serializer contains a nested creatable and writable serializer: PvGradingDetailsSerializer.
    By default, nested serializers provide the ability to only retrieve data;
    To make them writable and updatable you must override the create and update methods in the parent serializer.

    This serializer sometimes can contain OrderedDict instance types due to its 'validate_only' nature.
    Because of this, each 'get' override must check the instance type before creating queries
    """

    name = serializers.CharField(error_messages={"blank": "Enter a product name"})
    description = serializers.CharField(max_length=280, allow_blank=True, required=False)
    is_good_controlled = KeyValueChoiceField(choices=GoodControlled.choices, allow_null=True)
    control_list_entries = ControlListEntryField(required=False, many=True, allow_null=True, allow_empty=True)
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    status = KeyValueChoiceField(read_only=True, choices=GoodStatus.choices)
    not_sure_details_details = serializers.CharField(allow_blank=True, required=False)
    is_pv_graded = KeyValueChoiceField(
        choices=GoodPvGraded.choices, error_messages={"required": strings.Goods.FORM_DEFAULT_ERROR_RADIO_REQUIRED}
    )
    pv_grading_details = PvGradingDetailsSerializer(allow_null=True, required=False)
    is_document_available = serializers.BooleanField(allow_null=True, required=False, default=None)
    no_document_comments = serializers.CharField(allow_blank=True, required=False)
    is_document_sensitive = serializers.BooleanField(allow_null=True, required=False, default=None)
    product_description = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    item_category = KeyValueChoiceField(
        choices=ItemCategory.choices, error_messages={"required": strings.Goods.FORM_NO_ITEM_CATEGORY_SELECTED}
    )
    is_military_use = KeyValueChoiceField(choices=MilitaryUse.choices, required=False)
    is_component = KeyValueChoiceField(choices=Component.choices, allow_null=True, allow_blank=True, required=False)
    uses_information_security = serializers.BooleanField(allow_null=True, required=False, default=None)
    modified_military_use_details = serializers.CharField(
        allow_null=True, required=False, allow_blank=True, max_length=2000
    )
    component_details = serializers.CharField(allow_null=True, required=False, allow_blank=True, max_length=2000)
    information_security_details = serializers.CharField(
        allow_null=True, required=False, allow_blank=True, max_length=2000
    )
    software_or_technology_details = serializers.CharField(
        allow_null=True, required=False, allow_blank=True, max_length=2000
    )
    firearm_details = FirearmDetailsSerializer(allow_null=True, required=False)
    has_security_features = serializers.BooleanField(allow_null=True, required=False, default=None)
    security_feature_details = serializers.CharField(allow_null=True, required=False, allow_blank=True, max_length=2000)
    has_declared_at_customs = serializers.BooleanField(allow_null=True, required=False, default=None)
    design_details = serializers.CharField(allow_null=True, required=False, allow_blank=True, max_length=2000)

    class Meta:
        model = Good
        fields = (
            "id",
            "name",
            "description",
            "is_good_controlled",
            "control_list_entries",
            "part_number",
            "no_part_number_comments",
            "organisation",
            "status",
            "not_sure_details_details",
            "is_pv_graded",
            "pv_grading_details",
            "is_document_available",
            "is_document_sensitive",
            "product_description",
            "no_document_comments",
            "comment",
            "report_summary",
            "item_category",
            "is_military_use",
            "is_component",
            "uses_information_security",
            "modified_military_use_details",
            "component_details",
            "information_security_details",
            "software_or_technology_details",
            "firearm_details",
            "has_security_features",
            "security_feature_details",
            "has_declared_at_customs",
            "design_details",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self, "initial_data"):
            if not self.initial_data.get("control_list_entries") and not self.partial:
                self.initial_data["control_list_entries"] = []

        if self.get_initial().get("is_military_use"):
            is_military_use = self.get_initial().get("is_military_use")
            # if military answer is not "yes_modified" then remove the irrelevant details
            if is_military_use in [MilitaryUse.YES_DESIGNED, MilitaryUse.NO] and hasattr(self, "initial_data"):
                self.initial_data.pop("modified_military_use_details")

        if self.get_initial().get("uses_information_security"):
            # if information security is False then remove the irrelevant details
            if not str_to_bool(self.get_initial().get("uses_information_security")) and hasattr(self, "initial_data"):
                self.initial_data.pop("information_security_details")

        if self.get_initial().get("firearm_details"):
            firearm_details = self.get_initial().get("firearm_details")
            # Remove the dependent nested fields in the data if irrelevant based on the parent option selected
            if "is_covered_by_firearm_act_section_one_two_or_five" in firearm_details:
                # Remove the certificate number and expiry date if the answer is a No
                if firearm_details.get("is_covered_by_firearm_act_section_one_two_or_five") != "Yes":
                    if "section_certificate_number" in firearm_details:
                        firearm_details.pop("section_certificate_number")
                    if "section_certificate_date_of_expiry" in firearm_details:
                        firearm_details.pop("section_certificate_date_of_expiry")

            if "serial_numbers_available" in firearm_details:
                # Keep only the details relevant for the answer
                if FirearmGoodDetails.SerialNumberAvailability.has_serial_numbers(
                    firearm_details["serial_numbers_available"]
                ):
                    firearm_details.pop("no_identification_markings_details")

        self.goods_query_case = (
            GoodsQuery.objects.filter(good=self.instance).first() if isinstance(self.instance, Good) else None
        )

    def validate(self, data):
        if data.get("is_component") and data["is_component"] not in [Component.NO, "None"]:
            component_detail_fields = {
                Component.YES_DESIGNED: "designed_details",
                Component.YES_MODIFIED: "modified_details",
                Component.YES_GENERAL_PURPOSE: "general_details",
            }
            # Map the specific details field that was filled in to the single component_details field on the model
            data["component_details"] = self.initial_data[component_detail_fields[data["is_component"]]]

        return super().validate(data)

    def create(self, validated_data):
        if validated_data.get("pv_grading_details"):
            validated_data["pv_grading_details"] = GoodCreateSerializer._create_pv_grading_details(
                validated_data["pv_grading_details"]
            )

        if validated_data.get("firearm_details"):
            validated_data["firearm_details"] = GoodCreateSerializer._create_firearm_details(
                validated_data["firearm_details"]
            )

        return super(GoodCreateSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.is_good_controlled = validated_data.get("is_good_controlled", instance.is_good_controlled)
        instance.part_number = validated_data.get("part_number", instance.part_number)
        instance.no_part_number_comments = validated_data.get(
            "no_part_number_comments", instance.no_part_number_comments
        )
        instance.status = validated_data.get("status", instance.status)
        instance.is_pv_graded = validated_data.get("is_pv_graded", instance.is_pv_graded)
        instance.is_document_available = validated_data.get("is_document_available", instance.is_document_available)
        instance.no_document_comments = validated_data.get("no_document_comments", instance.no_document_comments)
        instance.is_document_sensitive = validated_data.get("is_document_sensitive", instance.is_document_sensitive)
        instance.product_description = validated_data.get("product_description", instance.product_description)

        if "control_list_entries" in validated_data:
            instance.control_list_entries.set(validated_data["control_list_entries"])

        if validated_data.get("is_pv_graded"):
            instance.pv_grading_details = GoodCreateSerializer._create_update_or_delete_pv_grading_details(
                is_pv_graded=instance.is_pv_graded == GoodPvGraded.YES,
                pv_grading_details=validated_data.get("pv_grading_details"),
                instance=instance.pv_grading_details,
            )

        is_military_use = validated_data.get("is_military_use")
        # if military answer has changed, then set the new value and the details field
        if is_military_use is not None and is_military_use != instance.is_military_use:
            instance.is_military_use = is_military_use
            instance.modified_military_use_details = validated_data.get("modified_military_use_details")
        instance.modified_military_use_details = validated_data.get(
            "modified_military_use_details", instance.modified_military_use_details
        )
        # if military answer is not "yes_modified" then the details are set to None
        if instance.is_military_use in [MilitaryUse.YES_DESIGNED, MilitaryUse.NO]:
            instance.modified_military_use_details = None

        is_component = validated_data.get("is_component")
        # if component answer has changed, then set the new value and the details field
        if is_component is not None and is_component != instance.is_component:
            instance.is_component = is_component
            instance.component_details = validated_data.get("component_details")
        instance.component_details = validated_data.get("component_details", instance.component_details)

        uses_information_security = validated_data.get("uses_information_security")
        # if information security has changed, then set the new value and the details field
        if uses_information_security is not None and uses_information_security != instance.uses_information_security:
            instance.uses_information_security = uses_information_security
            instance.information_security_details = validated_data.get(
                "information_security_details", instance.information_security_details
            )
        instance.information_security_details = validated_data.get("information_security_details", "")

        # When information security is No, then clear the details field and remove so it is not validated again
        if uses_information_security is False:
            instance.information_security_details = ""
        else:
            instance.information_security_details = validated_data.get(
                "information_security_details", instance.information_security_details
            )
        # If the information security details have changed
        instance.information_security_details = validated_data.get(
            "information_security_details", instance.information_security_details
        )

        has_security_features = validated_data.get("has_security_features")
        # if information security has changed, then set the new value and the details field
        if has_security_features is not None and has_security_features != instance.has_security_features:
            instance.has_security_features = has_security_features
            instance.security_feature_details = validated_data.get(
                "security_feature_details", instance.information_security_details
            )

        if has_security_features is False:
            instance.security_feature_details = ""
        else:
            instance.security_feature_details = validated_data.get(
                "security_feature_details", instance.security_feature_details
            )

        has_declared_at_customs = validated_data.get("has_declared_at_customs")
        if has_declared_at_customs is not None and has_declared_at_customs != instance.has_declared_at_customs:
            instance.has_declared_at_customs = has_declared_at_customs

        design_details = validated_data.get("design_details")
        if design_details is not None and design_details != instance.design_details:
            instance.design_details = design_details

        software_or_technology_details = validated_data.get("software_or_technology_details")
        if software_or_technology_details:
            instance.software_or_technology_details = software_or_technology_details

        if instance.item_category in ItemCategory.group_two:
            firearm_details = validated_data.get("firearm_details")
            if firearm_details:
                instance.firearm_details = GoodCreateSerializer._update_firearm_details(
                    firearm_details=firearm_details, instance=instance.firearm_details
                )

        instance.save()
        return instance

    @staticmethod
    def _create_update_or_delete_pv_grading_details(is_pv_graded=False, pv_grading_details=None, instance=None):
        """
        Creates/Updates/Deletes PV Grading Details depending on the parameters supplied
        :param is_pv_graded: If the good is not PV Graded, ensure there are no PV Grading Details
        :param pv_grading_details: The PV Grading Details to be created or updated
        :param instance: If supplied, it implies the instance of PV Grading Details to be updated or deleted
        :return:
        """
        if not is_pv_graded and instance:
            return GoodCreateSerializer._delete_pv_grading_details(instance)

        if pv_grading_details:
            if instance:
                return GoodCreateSerializer._update_pv_grading_details(pv_grading_details, instance)

            return GoodCreateSerializer._create_pv_grading_details(pv_grading_details)

        return None

    @staticmethod
    def _create_pv_grading_details(pv_grading_details):
        return PvGradingDetailsSerializer.create(PvGradingDetailsSerializer(), validated_data=pv_grading_details)

    @staticmethod
    def _update_pv_grading_details(pv_grading_details, instance):
        return PvGradingDetailsSerializer.update(
            PvGradingDetailsSerializer(), validated_data=pv_grading_details, instance=instance
        )

    @staticmethod
    def _delete_pv_grading_details(instance):
        instance.delete()
        return None

    @staticmethod
    def _create_firearm_details(firearm_details):
        return FirearmDetailsSerializer.create(FirearmDetailsSerializer(), validated_data=firearm_details)

    @staticmethod
    def _update_firearm_details(firearm_details, instance):
        return FirearmDetailsSerializer.update(
            FirearmDetailsSerializer(), validated_data=firearm_details, instance=instance
        )


class GoodDocumentAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = ("id", "is_document_available", "no_document_comments")


class GoodDocumentSensitivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = ("id", "is_document_sensitive")


class GoodMissingDocumentSerializer(serializers.ModelSerializer):
    missing_document_reason = KeyValueChoiceField(
        choices=GoodMissingDocumentReasons.choices,
        allow_blank=False,
        required=True,
        error_messages={"invalid_choice": strings.Goods.INVALID_MISSING_DOCUMENT_REASON},
    )

    class Meta:
        model = Good
        fields = ("id", "missing_document_reason")


class GoodDocumentCreateSerializer(serializers.ModelSerializer):
    good = serializers.PrimaryKeyRelatedField(queryset=Good.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=ExporterUser.objects.all())
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = GoodDocument
        fields = ("name", "s3_key", "user", "organisation", "size", "good", "description")

    def create(self, validated_data):
        good_document = super(GoodDocumentCreateSerializer, self).create(validated_data)
        good_document.save()
        process_document(good_document)
        return good_document


class GoodDocumentViewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    name = serializers.CharField()
    description = serializers.CharField()
    user = ExporterUserSimpleSerializer()
    s3_key = serializers.SerializerMethodField()
    safe = serializers.BooleanField()

    def get_s3_key(self, instance):
        return instance.s3_key if instance.safe else "File not ready"


class SimpleGoodDocumentViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodDocument
        fields = ("id", "name", "description", "size", "safe")


class GoodsFlagSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


class GoodControlListEntryViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodControlListEntry
        fields = "__all__"


class GoodOnApplicationSerializer(serializers.ModelSerializer):
    queue = serializers.SerializerMethodField()
    reference = serializers.ReadOnlyField(source="application.reference_code")
    control_list_entries = serializers.SerializerMethodField()
    wassenaar = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()
    submitted_at = serializers.ReadOnlyField(source="application.submitted_at")
    goods_starting_point = serializers.ReadOnlyField(source="application.standardapplication.goods_starting_point")
    regime_entries = RegimeEntrySerializer(many=True, read_only=True)

    class Meta:
        model = GoodOnApplication
        fields = (
            "id",
            "queue",
            "application",
            "reference",
            "good",
            "report_summary",
            "quantity",
            "unit",
            "value",
            "control_list_entries",
            "destinations",
            "wassenaar",
            "submitted_at",
            "goods_starting_point",
            "regime_entries",
        )

    def get_queue(self, obj):
        queue = obj.application.queues.first()
        return queue.id if queue else None

    def get_control_list_entries(self, obj):
        return [cle.rating for cle in obj.get_control_list_entries().all()]

    def get_wassenaar(self, obj):
        return obj.good.flags.filter(name="WASSENAAR").exists()

    def get_destinations(self, obj):
        destinations = (
            obj.application.parties.filter(
                deleted_at__isnull=True,
            )
            .values(
                "party__country__name",
            )
            .distinct()
        )

        return [dest["party__country__name"] for dest in destinations]


class GoodSerializerInternal(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    part_number = serializers.CharField()
    no_part_number_comments = serializers.CharField()
    control_list_entries = ControlListEntrySerializer(many=True)
    comment = serializers.CharField()
    is_good_controlled = KeyValueChoiceField(choices=GoodControlled.choices)
    report_summary = serializers.CharField(allow_blank=True, required=False)
    report_summary_prefix = ReportSummaryPrefixSerializer()
    report_summary_subject = ReportSummarySubjectSerializer()
    flags = GoodsFlagSerializer(many=True)
    documents = serializers.SerializerMethodField()
    is_pv_graded = serializers.CharField()
    grading_comment = serializers.CharField()
    pv_grading_details = PvGradingDetailsSerializer(allow_null=True, required=False)
    status = KeyValueChoiceField(choices=GoodStatus.choices)
    item_category = KeyValueChoiceField(choices=ItemCategory.choices)
    is_military_use = KeyValueChoiceField(choices=MilitaryUse.choices)
    is_component = KeyValueChoiceField(choices=Component.choices)
    uses_information_security = serializers.BooleanField()
    modified_military_use_details = serializers.CharField()
    component_details = serializers.CharField()
    information_security_details = serializers.CharField()
    is_document_available = serializers.BooleanField()
    is_document_sensitive = serializers.BooleanField()
    no_document_comments = serializers.CharField()
    software_or_technology_details = serializers.CharField()
    firearm_details = FirearmDetailsSerializer(allow_null=True, required=False)
    is_precedent = serializers.BooleanField(required=False, default=False)
    product_description = serializers.CharField()

    def get_documents(self, instance):
        documents = instance.gooddocument_set.all()
        return SimpleGoodDocumentViewSerializer(documents, many=True).data


class GoodSerializerInternalIncludingPrecedents(GoodSerializerInternal):
    precedents = GoodOnApplicationSerializer(many=True, source="get_precedents")


class TinyGoodDetailsSerializer(serializers.ModelSerializer):
    firearm_details = FirearmDetailsSerializer(read_only=True)

    class Meta:
        model = Good
        fields = (
            "id",
            "item_category",
            "is_military_use",
            "is_component",
            "uses_information_security",
            "modified_military_use_details",
            "component_details",
            "information_security_details",
            "software_or_technology_details",
            "firearm_details",
        )


class GoodSerializerExporter(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    control_list_entries = ControlListEntryField(many=True)
    part_number = serializers.CharField()
    no_part_number_comments = serializers.CharField()
    is_good_controlled = KeyValueChoiceField(choices=GoodControlled.choices)
    is_pv_graded = KeyValueChoiceField(choices=GoodPvGraded.choices)
    item_category = KeyValueChoiceField(choices=ItemCategory.choices)
    is_military_use = KeyValueChoiceField(choices=MilitaryUse.choices)
    is_component = KeyValueChoiceField(choices=Component.choices)
    uses_information_security = serializers.BooleanField()
    modified_military_use_details = serializers.CharField()
    component_details = serializers.CharField()
    information_security_details = serializers.CharField()
    pv_grading_details = PvGradingDetailsSerializer(allow_null=True, required=False)
    software_or_technology_details = serializers.CharField()
    firearm_details = FirearmDetailsSerializer(allow_null=True, required=False)
    precedents = GoodOnApplicationSerializer(many=True, source="get_precedents")
    has_security_features = serializers.BooleanField()
    security_feature_details = serializers.CharField()
    has_declared_at_customs = serializers.BooleanField()
    design_details = serializers.CharField()


class GoodSerializerExporterFullDetail(GoodSerializerExporter):
    case_id = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    is_document_available = serializers.BooleanField()
    is_document_sensitive = serializers.BooleanField()
    no_document_comments = serializers.CharField()
    product_description = serializers.CharField()
    status = KeyValueChoiceField(choices=GoodStatus.choices)
    query = serializers.SerializerMethodField()
    case_officer = serializers.SerializerMethodField()
    case_status = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(GoodSerializerExporterFullDetail, self).__init__(*args, **kwargs)
        self.goods_query = GoodsQuery.objects.filter(good=self.instance).first()

    def get_case_id(self, instance):
        return str(self.goods_query.id) if self.goods_query else None

    def get_documents(self, instance):
        documents = GoodDocument.objects.filter(good=instance)
        return SimpleGoodDocumentViewSerializer(documents, many=True).data

    def get_query(self, instance):
        from api.queries.goods_query.serializers import ExporterReadGoodQuerySerializer

        if self.goods_query:
            serializer = ExporterReadGoodQuerySerializer(
                instance=self.goods_query,
                context={"exporter_user": self.context.get("exporter_user"), "total_count": False},
            )
            return serializer.data

    def get_case_status(self, instance):
        if self.goods_query:
            return {
                "key": self.goods_query.status.status,
                "value": get_status_value_from_case_status_enum(self.goods_query.status.status),
            }

    def get_case_officer(self, instance):
        if self.goods_query:
            return GovUserSimpleSerializer(self.goods_query.case_officer).data


class ControlGoodOnApplicationSerializer(GoodControlReviewSerializer):

    is_precedent = serializers.BooleanField(required=False, default=False)
    is_wassenaar = serializers.BooleanField(required=False, default=False)
    regime_entries = PrimaryKeyRelatedField(
        many=True,
        queryset=RegimeEntry.objects.all(),
        required=False,  # not required for backwards compatibility reasons so that the old UI will still work
    )
    report_summary_prefix = PrimaryKeyRelatedField(
        required=False, allow_null=True, queryset=ReportSummaryPrefix.objects.all()
    )
    report_summary_subject = PrimaryKeyRelatedField(
        required=False, allow_null=True, queryset=ReportSummarySubject.objects.all()
    )

    class Meta(GoodControlReviewSerializer.Meta):
        model = GoodOnApplication
        fields = GoodControlReviewSerializer.Meta.fields + (
            "end_use_control",
            "is_precedent",
            "is_wassenaar",
            "regime_entries",
            "report_summary_prefix",
            "report_summary_subject",
        )

    def update(self, instance, validated_data):
        super().update(instance, validated_data)
        if instance.good.status == GoodStatus.VERIFIED:
            instance.good.control_list_entries.add(*validated_data["control_list_entries"])
        else:
            instance.good.status = GoodStatus.VERIFIED
            instance.good.control_list_entries.set(validated_data["control_list_entries"])
            instance.good.flags.remove(SystemFlags.GOOD_NOT_YET_VERIFIED_ID)

        instance.good.report_summary = validated_data.get("report_summary", instance.report_summary)

        if validated_data.get("report_summary_prefix", None):
            prefix_uuid = validated_data["report_summary_prefix"].id
            instance.good.report_summary_prefix = ReportSummaryPrefix.objects.get(id=prefix_uuid)
        if validated_data.get("report_summary_subject", None):
            subject_uuid = validated_data["report_summary_subject"].id
            instance.good.report_summary_subject = ReportSummarySubject.objects.get(id=subject_uuid)

        instance.good.save()

        return instance


class ClcControlGoodSerializer(GoodControlReviewSerializer):
    class Meta(GoodControlReviewSerializer.Meta):
        model = Good

    def update(self, instance, validated_data):
        validated_data = {"status": GoodStatus.VERIFIED, **validated_data}
        super().update(instance, validated_data)
        instance.flags.remove(SystemFlags.GOOD_NOT_YET_VERIFIED_ID)
        return instance
