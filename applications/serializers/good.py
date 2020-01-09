from lite_content.lite_api import strings
from rest_framework import serializers
from rest_framework.fields import DecimalField, ChoiceField, BooleanField
from rest_framework.relations import PrimaryKeyRelatedField

from applications.models import StandardApplication, GoodOnApplication
from conf.serializers import KeyValueChoiceField
from goods.models import Good
from goods.serializers import GoodWithFlagsSerializer, GoodSerializer
from static.units.enums import Units


class GoodOnApplicationWithFlagsViewSerializer(serializers.ModelSerializer):
    good = GoodWithFlagsSerializer(read_only=True)
    unit = KeyValueChoiceField(choices=Units.choices)

    class Meta:
        model = GoodOnApplication
        fields = (
            "id",
            "good",
            "quantity",
            "unit",
            "value",
        )


class GoodOnApplicationViewSerializer(serializers.ModelSerializer):
    good = GoodSerializer(read_only=True)
    unit = KeyValueChoiceField(choices=Units.choices)

    class Meta:
        model = GoodOnApplication
        fields = ("id", "good", "application", "quantity", "unit", "value", "is_good_incorporated")


class GoodOnApplicationCreateSerializer(serializers.ModelSerializer):
    good = PrimaryKeyRelatedField(queryset=Good.objects.all())
    application = PrimaryKeyRelatedField(queryset=StandardApplication.objects.all())
    value = DecimalField(max_digits=256, decimal_places=2, error_messages={"invalid": strings.Goods.INVALID_VALUE})
    quantity = DecimalField(
        max_digits=256, decimal_places=6, error_messages={"invalid": strings.Goods.INVALID_QUANTITY}
    )
    unit = ChoiceField(
        choices=Units.choices,
        error_messages={"required": strings.Goods.REQUIRED_UNIT, "invalid_choice": strings.Goods.REQUIRED_UNIT},
    )
    is_good_incorporated = BooleanField(required=True, error_messages={"required": strings.Goods.INCORPORATED_ERROR})

    class Meta:
        model = GoodOnApplication
        fields = ("id", "good", "application", "value", "quantity", "unit", "is_good_incorporated")
