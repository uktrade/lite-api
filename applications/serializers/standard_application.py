from rest_framework import serializers
from rest_framework.fields import CharField

from applications.enums import GoodsCategory, YesNoChoiceType
from applications.mixins.serializers import PartiesSerializerMixin
from applications.models import StandardApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from applications.serializers.good import GoodOnApplicationViewSerializer
from conf.serializers import KeyValueChoiceField
from lite_content.lite_api import strings


class StandardApplicationViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()
    goods_categories = serializers.SerializerMethodField()

    def get_goods_categories(self, instance):
        # Return a formatted key, value format of GoodsCategories
        # Order according to the choices in GoodsCategory
        return_value = [{"key": x, "value": GoodsCategory.get_text(x)} for x in instance.goods_categories or []]
        return sorted(return_value, key=lambda i: [x[0] for x in GoodsCategory.choices].index(i["key"]))

    class Meta:
        model = StandardApplication
        fields = (
            GenericApplicationViewSerializer.Meta.fields
            + PartiesSerializerMixin.Meta.fields
            + (
                "goods",
                "have_you_been_informed",
                "reference_number_on_information_form",
                "goods_categories",
                "activity",
                "usage",
                "destinations",
                "additional_documents",
            )
        )


class StandardApplicationCreateSerializer(GenericApplicationCreateSerializer):
    goods_categories = serializers.MultipleChoiceField(
        choices=GoodsCategory.choices, required=False, allow_null=True, allow_blank=True, allow_empty=True
    )

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "name",
            "case_type",
            "export_type",
            "have_you_been_informed",
            "reference_number_on_information_form",
            "goods_categories",
            "organisation",
            "status",
        )


class StandardApplicationUpdateSerializer(GenericApplicationUpdateSerializer):
    reference_number_on_information_form = CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    goods_categories = serializers.MultipleChoiceField(
        choices=GoodsCategory.choices, required=False, allow_null=True, allow_blank=True, allow_empty=True
    )

    is_military_end_use_controls = KeyValueChoiceField(choices=YesNoChoiceType.yes_no_choices, allow_blank=True,
                                                       allow_null=True)
    is_informed_wmd = KeyValueChoiceField(choices=YesNoChoiceType.yes_no_choices, allow_blank=True, allow_null=True)
    is_suspected_wmd = KeyValueChoiceField(choices=YesNoChoiceType.yes_no_choices, allow_blank=True, allow_null=True)
    is_eu_military = KeyValueChoiceField(choices=YesNoChoiceType.yes_no_na_choices, allow_blank=True, allow_null=True)

    military_end_use_controls_ref = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=2000
    )
    informed_wmd_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)
    suspected_wmd_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)

    class Meta:
        model = StandardApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + (
            "have_you_been_informed",
            "reference_number_on_information_form",
            "goods_categories",
            "is_military_end_use_controls",
            "military_end_use_controls_ref",
            "is_informed_wmd",
            "informed_wmd_ref",
            "is_suspected_wmd",
            "suspected_wmd_ref",
            "is_eu_military",
        )

    def update(self, instance, validated_data):
        if "goods_categories" in validated_data:
            instance.goods_categories = validated_data["goods_categories"]
        instance.have_you_been_informed = validated_data.get("have_you_been_informed", instance.have_you_been_informed)
        if instance.have_you_been_informed == "yes":
            instance.reference_number_on_information_form = validated_data.get(
                "reference_number_on_information_form", instance.reference_number_on_information_form,
            )
        else:
            instance.reference_number_on_information_form = None
        instance = super().update(instance, validated_data)
        return instance

    def validate(self, data):
        validated_data = super().validate(data)
        self._validate_dependent_ref_field(
            validated_data, "is_military_end_use_controls", "military_end_use_controls_ref"
        )
        self._validate_dependent_ref_field(validated_data, "is_informed_wmd", "informed_wmd_ref")
        self._validate_dependent_ref_field(validated_data, "is_suspected_wmd", "suspected_wmd_ref")
        return validated_data

    @staticmethod
    def _validate_dependent_ref_field(validated_data, yes_no_field, ref_field):
        yes_no_field_val = validated_data.get(yes_no_field)
        if not yes_no_field_val:
            raise serializers.ValidationError({yes_no_field: "Required!"})
        if yes_no_field_val == YesNoChoiceType.YES:
            if not validated_data.get(ref_field):
                raise serializers.ValidationError({ref_field: "Very bad"})
