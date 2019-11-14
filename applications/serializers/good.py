from rest_framework import serializers
from rest_framework.fields import DecimalField, ChoiceField
from rest_framework.relations import PrimaryKeyRelatedField

from applications.models import StandardApplication, \
    GoodOnApplication
from conf.serializers import KeyValueChoiceField
from content_strings.strings import get_string
from goods.models import Good
from goods.serializers import GoodWithFlagsSerializer, GoodSerializer
from static.units.enums import Units


class GoodOnApplicationWithFlagsViewSerializer(serializers.ModelSerializer):
    good = GoodWithFlagsSerializer(read_only=True)
    unit = KeyValueChoiceField(choices=Units.choices)

    class Meta:
        model = GoodOnApplication
        fields = ('id',
                  'good',
                  'quantity',
                  'unit',
                  'value',)


class GoodOnApplicationViewSerializer(serializers.ModelSerializer):
    good = GoodSerializer(read_only=True)
    unit = KeyValueChoiceField(choices=Units.choices)

    class Meta:
        model = GoodOnApplication
        fields = ('id',
                  'good',
                  'application',
                  'quantity',
                  'unit',
                  'value',)


class GoodOnApplicationCreateSerializer(serializers.ModelSerializer):
    good = PrimaryKeyRelatedField(queryset=Good.objects.all())
    application = PrimaryKeyRelatedField(queryset=StandardApplication.objects.all())
    quantity = DecimalField(max_digits=256, decimal_places=6,
                            error_messages={'invalid': get_string('goods.error_messages.invalid_qty')})
    value = DecimalField(max_digits=256, decimal_places=2,
                         error_messages={'invalid': get_string('goods.error_messages.invalid_value')}),
    unit = ChoiceField(choices=Units.choices, error_messages={
        'required': get_string('goods.error_messages.required_unit'),
        'invalid_choice': get_string('goods.error_messages.required_unit')})

    class Meta:
        model = GoodOnApplication
        fields = ('id',
                  'good',
                  'application',
                  'quantity',
                  'unit',
                  'value',)
