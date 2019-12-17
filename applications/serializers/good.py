import lite_content.lite_api.goods

from rest_framework import serializers
from rest_framework.fields import DecimalField, ChoiceField
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
        fields = (
            "id",
            "good",
            "application",
            "quantity",
            "unit",
            "value",
        )


class GoodOnApplicationCreateSerializer(serializers.ModelSerializer):
    good = PrimaryKeyRelatedField(queryset=Good.objects.all())
    application = PrimaryKeyRelatedField(queryset=StandardApplication.objects.all())
    quantity = DecimalField(
        max_digits=256, decimal_places=6, error_messages={"invalid": lite_content.lite_api.goods.Goods.ErrorMessages.INVALID_QTY},
    )
    value = (
        DecimalField(
            max_digits=256, decimal_places=2, error_messages={"invalid": lite_content.lite_api.goods.Goods.ErrorMessages.INVALID_VALUE},
        ),
    )
    unit = ChoiceField(
        choices=Units.choices,
        error_messages={
            "required": lite_content.lite_api.goods.Goods.ErrorMessages.REQUIRED_UNIT,
            "invalid_choice": lite_content.lite_api.goods.Goods.ErrorMessages.REQUIRED_UNIT,
        },
    )

    class Meta:
        model = GoodOnApplication
        fields = (
            "id",
            "good",
            "application",
            "quantity",
            "unit",
            "value",
        )
