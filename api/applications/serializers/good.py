from rest_framework import serializers
from rest_framework.fields import DecimalField, ChoiceField, BooleanField
from rest_framework.relations import PrimaryKeyRelatedField

from api.applications.models import BaseApplication, GoodOnApplication
from cases.enums import CaseTypeEnum
from cases.models import Case
from api.conf.serializers import KeyValueChoiceField
from api.goods.enums import ItemType
from api.goods.models import Good
from api.goods.serializers import GoodSerializerInternal
from api.licences.models import GoodOnLicence
from lite_content.lite_api import strings
from api.staticdata.units.enums import Units


class GoodOnStandardLicenceSerializer(serializers.ModelSerializer):
    quantity = serializers.FloatField(
        required=True,
        allow_null=False,
        min_value=0,
        error_messages={
            "null": strings.Licence.NULL_QUANTITY_ERROR,
            "min_value": strings.Licence.NEGATIVE_QUANTITY_ERROR,
        },
    )
    value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=True,
        allow_null=False,
        min_value=0,
        error_messages={"null": strings.Licence.NULL_VALUE_ERROR, "min_value": strings.Licence.NEGATIVE_VALUE_ERROR,},
    )

    class Meta:
        model = GoodOnLicence
        fields = (
            "id",
            "quantity",
            "value",
            "good",
            "licence",
        )

    def validate(self, data):
        if data["quantity"] > self.context.get("applied_for_quantity"):
            raise serializers.ValidationError({"quantity": strings.Licence.INVALID_QUANTITY_ERROR})
        return data


class GoodOnApplicationViewSerializer(serializers.ModelSerializer):
    good = GoodSerializerInternal(read_only=True)
    unit = KeyValueChoiceField(choices=Units.choices)
    flags = serializers.SerializerMethodField()

    class Meta:
        model = GoodOnApplication
        fields = (
            "id",
            "good",
            "application",
            "quantity",
            "unit",
            "value",
            "is_good_incorporated",
            "flags",
            "item_type",
            "other_item_type",
        )

    def get_flags(self, instance):
        return list(instance.good.flags.values("id", "name", "colour", "label"))


class GoodOnApplicationCreateSerializer(serializers.ModelSerializer):
    good = PrimaryKeyRelatedField(queryset=Good.objects.all())
    application = PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    value = DecimalField(max_digits=15, decimal_places=2, error_messages={"invalid": strings.Goods.INVALID_VALUE})
    quantity = DecimalField(max_digits=15, decimal_places=6, error_messages={"invalid": strings.Goods.INVALID_QUANTITY})
    unit = ChoiceField(
        choices=Units.choices,
        error_messages={"required": strings.Goods.REQUIRED_UNIT, "invalid_choice": strings.Goods.REQUIRED_UNIT},
    )
    is_good_incorporated = BooleanField(required=True, error_messages={"required": strings.Goods.INCORPORATED_ERROR})
    item_type = serializers.ChoiceField(choices=ItemType.choices, error_messages={"required": strings.Goods.ITEM_TYPE})
    other_item_type = serializers.CharField(
        max_length=100,
        error_messages={"required": strings.Goods.OTHER_ITEM_TYPE, "blank": strings.Goods.OTHER_ITEM_TYPE},
    )

    class Meta:
        model = GoodOnApplication
        fields = (
            "id",
            "good",
            "application",
            "value",
            "quantity",
            "unit",
            "is_good_incorporated",
            "item_type",
            "other_item_type",
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        case_type = Case.objects.get(id=self.initial_data["application"]).case_type
        # Exbition queries do not have the typical data for goods on applications that other goods do
        #  as a result, we have to set them as false when not required and vice versa for other applications
        if case_type.id == CaseTypeEnum.EXHIBITION.id:
            self.fields["value"].required = False
            self.fields["quantity"].required = False
            self.fields["unit"].required = False
            self.fields["is_good_incorporated"].required = False
            # If the user passes item_type forward as anything but other, we do not want to store "other_item_type"
            if not self.initial_data.get("item_type") == ItemType.OTHER:
                if isinstance(self.initial_data.get("other_item_type"), str):
                    del self.initial_data["other_item_type"]
                self.fields["other_item_type"].required = False
        else:
            self.fields["item_type"].required = False
            self.fields["other_item_type"].required = False

            if self.initial_data.get("unit") == Units.ITG:
                # If the good is intangible, the value and quantity become optional
                self.fields["value"].required = False
                self.fields["quantity"].required = False

                # If the quantity or value aren't set, they are defaulted to 1 and 0 respectively
                if not self.initial_data["quantity"]:
                    self.initial_data["quantity"] = 1
                if not self.initial_data["value"]:
                    self.initial_data["value"] = 0
