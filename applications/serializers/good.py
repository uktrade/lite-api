from rest_framework import serializers
from rest_framework.fields import DecimalField, ChoiceField, BooleanField
from rest_framework.relations import PrimaryKeyRelatedField

from applications.models import BaseApplication, GoodOnApplication
from cases.enums import CaseTypeEnum
from cases.models import Case
from conf.serializers import KeyValueChoiceField
from goods.enums import ItemType
from goods.models import Good
from goods.serializers import GoodSerializer
from lite_content.lite_api import strings
from static.units.enums import Units


class GoodOnApplicationViewSerializer(serializers.ModelSerializer):
    good = GoodSerializer(read_only=True)
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
        )

    def get_flags(self, instance):
        return list(instance.good.flags.values("id", "name"))


class GoodOnApplicationCreateSerializer(serializers.ModelSerializer):
    good = PrimaryKeyRelatedField(queryset=Good.objects.all())
    application = PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    value = DecimalField(max_digits=256, decimal_places=2, error_messages={"invalid": strings.Goods.INVALID_VALUE})
    quantity = DecimalField(
        max_digits=256, decimal_places=6, error_messages={"invalid": strings.Goods.INVALID_QUANTITY}
    )
    unit = ChoiceField(
        choices=Units.choices,
        error_messages={"required": strings.Goods.REQUIRED_UNIT, "invalid_choice": strings.Goods.REQUIRED_UNIT},
    )
    is_good_incorporated = BooleanField(required=True, error_messages={"required": strings.Goods.INCORPORATED_ERROR})
    item_type = serializers.ChoiceField(choices=ItemType.choices)
    other_item_type = serializers.CharField(max_length=100)

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
        if case_type.id == CaseTypeEnum.EXHIBITION.id:
            self.fields["value"].required = False
            self.fields["quantity"].required = False
            self.fields["unit"].required = False
            self.fields["is_good_incorporated"].required = False
            if self.initial_data.get("item_type") and not self.initial_data["item_type"] == ItemType.OTHER:
                if self.initial_data.get("other_item_type"):
                    del self.initial_data["other_item_type"]
                self.fields["other_item_type"].required = False
        else:
            self.fields["item_type"].required = False
            self.fields["other_item_type"].required = False
