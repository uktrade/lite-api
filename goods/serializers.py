from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from conf.helpers import str_to_bool
from goods.enums import GoodStatus, GoodControlled
from goods.models import Good
from organisations.models import Organisation


class GoodSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=280)
    is_good_controlled = serializers.ChoiceField(choices=GoodControlled.choices)
    is_good_end_product = serializers.BooleanField()
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    status = serializers.ChoiceField(choices=GoodStatus.choices)

    class Meta:
        model = Good
        fields = ('id',
                  'description',
                  'is_good_controlled',
                  'control_code',
                  'is_good_end_product',
                  'part_number',
                  'organisation',
                  'status',
                  )

    def __init__(self, *args, **kwargs):
        super(GoodSerializer, self).__init__(*args, **kwargs)

        # import pdb; pdb.set_trace()
        # Only validate the control code if the good is controlled
        if str_to_bool(self.get_initial().get('is_good_controlled')) is True:
            self.fields['control_code'] = serializers.CharField(required=True)

    def update(self, instance, validated_data):
        instance.description = validated_data.get('description', instance.description)
        instance.is_good_controlled = validated_data.get('is_good_controlled', instance.is_good_controlled)
        instance.control_code = validated_data.get('control_code', instance.control_code)
        instance.is_good_end_product = validated_data.get('is_good_end_product', instance.is_good_end_product)
        instance.part_number = validated_data.get('part_number', instance.part_number)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance
