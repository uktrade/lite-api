from django.utils import timezone
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from common.libraries import (
    initialize_good_or_goods_type_control_list_entries_serializer,
    update_good_or_goods_type_control_list_entries_details,
)
from conf.helpers import str_to_bool
from conf.serializers import KeyValueChoiceField, ControlListEntryField
from documents.libraries.process_document import process_document
from goods.enums import (
    GoodStatus,
    GoodControlled,
    GoodPvGraded,
    PvGrading,
    ItemCategory,
    MilitaryUse,
    Component,
    FirearmGoodType,
)
from goods.helpers import (
    validate_military_use,
    validate_component_details,
    validate_identification_markings,
    validate_section_certificate_number_and_expiry_date,
)
from goods.models import Good, GoodDocument, PvGradingDetails, FirearmGoodDetails
from gov_users.serializers import GovUserSimpleSerializer
from lite_content.lite_api import strings
from organisations.models import Organisation
from picklists.models import PicklistItem
from queries.goods_query.models import GoodsQuery
from static.control_list_entries.serializers import ControlListEntrySerializer
from static.missing_document_reasons.enums import GoodMissingDocumentReasons
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum
from users.models import ExporterUser
from users.serializers import ExporterUserSimpleSerializer


class PvGradingDetailsSerializer(serializers.ModelSerializer):
    grading = KeyValueChoiceField(choices=PvGrading.choices, allow_null=True, allow_blank=True)
    custom_grading = serializers.CharField(allow_blank=True, allow_null=True)
    prefix = serializers.CharField(allow_blank=True, allow_null=True)
    suffix = serializers.CharField(allow_blank=True, allow_null=True)
    issuing_authority = serializers.CharField(allow_blank=False, allow_null=False)
    reference = serializers.CharField(allow_blank=False, allow_null=False)
    date_of_issue = serializers.DateField(
        allow_null=False,
        error_messages={"invalid": "Enter the products date of issue and include a day, month, year."},
    )

    class Meta:
        model = PvGradingDetails
        fields = (
            "grading",
            "custom_grading",
            "prefix",
            "suffix",
            "issuing_authority",
            "reference",
            "date_of_issue",
        )

    def validate(self, data):
        validated_data = super(PvGradingDetailsSerializer, self).validate(data)

        if not validated_data.get("grading") and not validated_data.get("custom_grading"):
            raise serializers.ValidationError({"custom_grading": strings.Goods.NO_CUSTOM_GRADING_ERROR})

        if validated_data.get("grading") and validated_data.get("custom_grading"):
            raise serializers.ValidationError(
                {"custom_grading": strings.Goods.PROVIDE_ONLY_GRADING_OR_CUSTOM_GRADING_ERROR}
            )

        return validated_data


class FirearmDetailsSerializer(serializers.ModelSerializer):
    type = KeyValueChoiceField(
        choices=FirearmGoodType.choices, allow_null=False, error_messages={"null": strings.Goods.FIREARM_GOOD_NO_TYPE},
    )
    year_of_manufacture = serializers.IntegerField(
        error_messages={"invalid": strings.Goods.FIREARM_GOOD_NO_YEAR_OF_MANUFACTURE},
    )
    calibre = serializers.CharField(error_messages={"blank": strings.Goods.FIREARM_GOOD_NO_CALIBRE}, max_length=15)
    # this refers specifically to section 1, 2 or 5 of firearms act 1968
    is_covered_by_firearm_act_section_one_two_or_five = serializers.BooleanField(allow_null=True, required=False)
    section_certificate_number = serializers.CharField(
        allow_blank=True, allow_null=True, required=False, max_length=100
    )
    section_certificate_date_of_expiry = serializers.DateField(
        allow_null=True, required=False, error_messages={"invalid": strings.Goods.FIREARM_GOOD_NO_EXPIRY_DATE}
    )
    has_identification_markings = serializers.BooleanField(allow_null=True, required=False,)
    identification_markings_details = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=2000
    )
    no_identification_markings_details = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=2000
    )

    class Meta:
        model = FirearmGoodDetails
        fields = (
            "type",
            "year_of_manufacture",
            "calibre",
            "is_covered_by_firearm_act_section_one_two_or_five",
            "section_certificate_number",
            "section_certificate_date_of_expiry",
            "has_identification_markings",
            "identification_markings_details",
            "no_identification_markings_details",
        )

    def validate(self, data):
        validated_data = super(FirearmDetailsSerializer, self).validate(data)

        # Year of manufacture should be in the past and a valid year
        year_of_manufacture = validated_data.get("year_of_manufacture")
        if year_of_manufacture:
            if year_of_manufacture > timezone.now().date().year:
                raise serializers.ValidationError(
                    {"year_of_manufacture": strings.Goods.FIREARM_GOOD_YEAR_MUST_BE_IN_PAST}
                )
            # Oldest firearm/ammunition in the world could date back to the 9th century - do not allow negative years
            if year_of_manufacture < 800:
                raise serializers.ValidationError(
                    {"year_of_manufacture": strings.Goods.FIREARM_GOOD_YEAR_MUST_BE_VALID}
                )

        # Firearms act validation - mandatory question
        if (
            "is_covered_by_firearm_act_section_one_two_or_five" in data
            and data.get("is_covered_by_firearm_act_section_one_two_or_five") is None
        ):
            raise serializers.ValidationError(
                {"is_covered_by_firearm_act_section_one_two_or_five": [strings.Goods.FIREARM_GOOD_NO_SECTION]}
            )

        # Section certificate number and date of expiry are mandatory if the answer to the firearms act question is True
        if validated_data.get("is_covered_by_firearm_act_section_one_two_or_five"):
            validate_section_certificate_number_and_expiry_date(validated_data)

        # Identification markings - mandatory question
        validate_identification_markings(validated_data)

        return validated_data

    def update(self, instance, validated_data):
        instance.type = validated_data.get("type", instance.type)
        instance.year_of_manufacture = validated_data.get("year_of_manufacture", instance.year_of_manufacture)
        instance.calibre = validated_data.get("calibre", instance.calibre)

        is_covered_by_firearms_act = validated_data.get("is_covered_by_firearm_act_section_one_two_or_five")
        # if the answer to the firearms act has changed, then set the new value and the certificate and date fields
        if (
            is_covered_by_firearms_act is not None
            and is_covered_by_firearms_act != instance.is_covered_by_firearm_act_section_one_two_or_five
        ):
            instance.is_covered_by_firearm_act_section_one_two_or_five = is_covered_by_firearms_act
            # Clear the date and certificate fields if the answer has changed to a No
            if not instance.is_covered_by_firearm_act_section_one_two_or_five:
                instance.section_certificate_number = ""
                instance.section_certificate_date_of_expiry = None

        # Update just the certificate and expiryy date fields if changed
        instance.section_certificate_number = validated_data.get(
            "section_certificate_number", instance.section_certificate_number
        )
        instance.section_certificate_date_of_expiry = validated_data.get(
            "section_certificate_date_of_expiry", instance.section_certificate_date_of_expiry
        )

        has_markings = validated_data.get("has_identification_markings")
        # if the answer to the identification markings question has changed
        if has_markings is not None and has_markings != instance.has_identification_markings:
            instance.has_identification_markings = has_markings
            # If changed to Yes, clear the no_identification_markings_details field
            if has_markings:
                instance.no_identification_markings_details = ""
                instance.identification_markings_details = validated_data.get("identification_markings_details")
            else:
                instance.identification_markings_details = ""
                instance.no_identification_markings_details = validated_data.get("no_identification_markings_details")
        # Update just the identification marking details fields value if changed
        instance.identification_markings_details = validated_data.get(
            "identification_markings_details", instance.identification_markings_details
        )
        instance.no_identification_markings_details = validated_data.get(
            "no_identification_markings_details", instance.no_identification_markings_details
        )

        instance.save()
        return instance


class GoodListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    control_list_entries = ControlListEntrySerializer(many=True)
    part_number = serializers.CharField()
    status = KeyValueChoiceField(choices=GoodStatus.choices)


class GoodCreateSerializer(serializers.ModelSerializer):
    """
    This serializer contains a nested creatable and writable serializer: PvGradingDetailsSerializer.
    By default, nested serializers provide the ability to only retrieve data;
    To make them writable and updatable you must override the create and update methods in the parent serializer.

    This serializer sometimes can contain OrderedDict instance types due to its 'validate_only' nature.
    Because of this, each 'get' override must check the instance type before creating queries
    """

    description = serializers.CharField(
        max_length=280, error_messages={"blank": strings.Goods.FORM_DEFAULT_ERROR_TEXT_BLANK}
    )
    is_good_controlled = KeyValueChoiceField(
        choices=GoodControlled.choices, error_messages={"required": strings.Goods.FORM_DEFAULT_ERROR_RADIO_REQUIRED}
    )
    control_list_entries = ControlListEntryField(required=False, many=True, allow_null=True, allow_empty=True)
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    status = KeyValueChoiceField(read_only=True, choices=GoodStatus.choices)
    not_sure_details_details = serializers.CharField(allow_blank=True, required=False)
    missing_document_reason = KeyValueChoiceField(choices=GoodMissingDocumentReasons.choices, read_only=True)
    is_pv_graded = KeyValueChoiceField(
        choices=GoodPvGraded.choices, error_messages={"required": strings.Goods.FORM_DEFAULT_ERROR_RADIO_REQUIRED}
    )
    pv_grading_details = PvGradingDetailsSerializer(allow_null=True, required=False)
    item_category = KeyValueChoiceField(
        choices=ItemCategory.choices, error_messages={"required": strings.Goods.FORM_NO_ITEM_CATEGORY_SELECTED}
    )
    is_military_use = KeyValueChoiceField(choices=MilitaryUse.choices, required=False)
    is_component = KeyValueChoiceField(choices=Component.choices, allow_null=True, allow_blank=True, required=False,)
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

    class Meta:
        model = Good
        fields = (
            "id",
            "description",
            "is_good_controlled",
            "control_list_entries",
            "part_number",
            "organisation",
            "status",
            "not_sure_details_details",
            "is_pv_graded",
            "pv_grading_details",
            "missing_document_reason",
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
        )

    def __init__(self, *args, **kwargs):
        super(GoodCreateSerializer, self).__init__(*args, **kwargs)

        if self.get_initial().get("is_good_controlled") == GoodControlled.YES:
            self.fields["control_list_entries"] = ControlListEntryField(required=True, many=True)
        else:
            if hasattr(self, "initial_data"):
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
                if not str_to_bool(firearm_details.get("is_covered_by_firearm_act_section_one_two_or_five")):
                    firearm_details.pop("section_certificate_number")
                    firearm_details.pop("section_certificate_date_of_expiry")

            if "has_identification_markings" in firearm_details:
                # Keep only the details relevant for the yes/no answer
                if str_to_bool(firearm_details.get("has_identification_markings")):
                    firearm_details.pop("no_identification_markings_details")
                else:
                    firearm_details.pop("identification_markings_details")

        self.goods_query_case = (
            GoodsQuery.objects.filter(good=self.instance).first() if isinstance(self.instance, Good) else None
        )

    def validate(self, data):
        is_controlled_good = data.get("is_good_controlled") == GoodControlled.YES
        if is_controlled_good and not data.get("control_list_entries"):
            raise serializers.ValidationError(
                {"control_list_entries": [strings.Goods.CONTROL_LIST_ENTRY_IF_CONTROLLED_ERROR]}
            )

        # Get item category from the instance when it is not passed down on editing a good
        item_category = data.get("item_category") if "item_category" in data else self.instance.item_category

        if item_category not in ItemCategory.group_two:
            # NB! The order of validation should match the order of the forms so that the appropriate error is raised if the
            # user clicks Back
            # Validate software/technology details for products in group 3
            if "software_or_technology_details" in data and not data.get("software_or_technology_details"):
                raise serializers.ValidationError(
                    {
                        "software_or_technology_details": [
                            strings.Goods.FORM_NO_SOFTWARE_DETAILS
                            if item_category == ItemCategory.GROUP3_SOFTWARE
                            else strings.Goods.FORM_NO_TECHNOLOGY_DETAILS
                        ]
                    }
                )

            validate_military_use(data)

            # Validate component field on creation (using is_component_step sent by the form), and on editing a good
            # (using is_component)
            if (
                item_category in ItemCategory.group_one
                and ("is_component" in data or "is_component_step" in self.initial_data)
                and not data.get("is_component")
            ):
                raise serializers.ValidationError({"is_component": [strings.Goods.FORM_NO_COMPONENT_SELECTED]})

            # Validate component detail field if the answer was not 'No' using the initial data which contains all details
            # fields as passed by the form
            if data.get("is_component") and data["is_component"] not in [Component.NO, "None"]:
                valid_components = validate_component_details(self.initial_data)
                if not valid_components["is_valid"]:
                    raise serializers.ValidationError({valid_components["details_field"]: [valid_components["error"]]})
                # Map the specific details field that was filled in to the single component_details field on the model
                data["component_details"] = self.initial_data[valid_components["details_field"]]

            # Validate information security
            if "uses_information_security" in data and data.get("uses_information_security") is None:
                raise serializers.ValidationError(
                    {"uses_information_security": [strings.Goods.FORM_PRODUCT_DESIGNED_FOR_SECURITY_FEATURES]}
                )

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
        instance.description = validated_data.get("description", instance.description)
        instance.is_good_controlled = validated_data.get("is_good_controlled", instance.is_good_controlled)
        instance.control_list_entries.set(
            validated_data.get("control_list_entries", instance.control_list_entries.all())
        )
        instance.part_number = validated_data.get("part_number", instance.part_number)
        instance.status = validated_data.get("status", instance.status)
        instance.is_pv_graded = validated_data.get("is_pv_graded", instance.is_pv_graded)

        if validated_data.get("is_pv_graded"):
            instance.pv_grading_details = GoodCreateSerializer._create_update_or_delete_pv_grading_details(
                is_pv_graded=instance.is_pv_graded == GoodPvGraded.YES,
                pv_grading_details=validated_data.get("pv_grading_details"),
                instance=instance.pv_grading_details,
            )

        if instance.item_category not in ItemCategory.group_two:
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
            if (
                uses_information_security is not None
                and uses_information_security != instance.uses_information_security
            ):
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

            software_or_technology_details = validated_data.get("software_or_technology_details")
            if software_or_technology_details:
                instance.software_or_technology_details = software_or_technology_details
        else:
            firearm_details = validated_data.get("firearm_details")
            if firearm_details:
                instance.firearm_details = GoodCreateSerializer._update_firearm_details(
                    firearm_details=firearm_details, instance=instance.firearm_details,
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
            PvGradingDetailsSerializer(), validated_data=pv_grading_details, instance=instance,
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
            FirearmDetailsSerializer(), validated_data=firearm_details, instance=instance,
        )


class GoodMissingDocumentSerializer(serializers.ModelSerializer):
    missing_document_reason = KeyValueChoiceField(
        choices=GoodMissingDocumentReasons.choices,
        allow_blank=False,
        required=True,
        error_messages={"invalid_choice": strings.Goods.INVALID_MISSING_DOCUMENT_REASON},
    )

    class Meta:
        model = Good
        fields = (
            "id",
            "missing_document_reason",
        )


class GoodDocumentCreateSerializer(serializers.ModelSerializer):
    good = serializers.PrimaryKeyRelatedField(queryset=Good.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=ExporterUser.objects.all())
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = GoodDocument
        fields = (
            "name",
            "s3_key",
            "user",
            "organisation",
            "size",
            "good",
            "description",
        )

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

    def get_s3_key(self, instance):
        return instance.s3_key if instance.safe else "File not ready"


class SimpleGoodDocumentViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodDocument
        fields = (
            "id",
            "name",
            "description",
            "size",
            "safe",
        )


class GoodsFlagSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


class GoodSerializerInternal(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    part_number = serializers.CharField()
    control_list_entries = ControlListEntrySerializer(many=True)
    comment = serializers.CharField()
    is_good_controlled = KeyValueChoiceField(choices=GoodControlled.choices)
    report_summary = serializers.CharField()
    flags = GoodsFlagSerializer(many=True)
    documents = serializers.SerializerMethodField()
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
    missing_document_reason = KeyValueChoiceField(choices=GoodMissingDocumentReasons.choices)
    software_or_technology_details = serializers.CharField()
    firearm_details = FirearmDetailsSerializer(allow_null=True, required=False)

    def get_documents(self, instance):
        documents = GoodDocument.objects.filter(good=instance)
        return SimpleGoodDocumentViewSerializer(documents, many=True).data


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
    description = serializers.CharField()
    control_list_entries = ControlListEntryField(many=True)
    part_number = serializers.CharField()
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


class GoodSerializerExporterFullDetail(GoodSerializerExporter):
    case_id = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    missing_document_reason = KeyValueChoiceField(choices=GoodMissingDocumentReasons.choices)
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
        from queries.goods_query.serializers import ExporterReadGoodQuerySerializer

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


class ClcControlGoodSerializer(serializers.ModelSerializer):
    is_good_controlled = serializers.ChoiceField(
        choices=GoodControlled.choices,
        allow_null=False,
        required=True,
        write_only=True,
        error_messages={"null": "This field is required."},
    )
    control_list_entries = ControlListEntryField(required=False, allow_null=True, write_only=True, many=True)
    comment = serializers.CharField(allow_blank=True, max_length=500, required=True, allow_null=True)
    report_summary = serializers.CharField()

    class Meta:
        model = Good
        fields = (
            "is_good_controlled",
            "control_list_entries",
            "comment",
            "report_summary",
        )

    def __init__(self, *args, **kwargs):
        super(ClcControlGoodSerializer, self).__init__(*args, **kwargs)
        initialize_good_or_goods_type_control_list_entries_serializer(self)

    def update(self, instance, validated_data):
        instance.is_good_controlled = validated_data.get("is_good_controlled", instance.is_good_controlled)
        instance = update_good_or_goods_type_control_list_entries_details(instance, validated_data)
        instance.status = GoodStatus.VERIFIED
        instance.save()
        return instance
