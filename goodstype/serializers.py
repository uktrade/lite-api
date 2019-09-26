from rest_framework import serializers

from applications.models import OpenApplication
from conf.helpers import str_to_bool
from flags.enums import FlagStatuses
from goodstype.models import GoodsType


class GoodsTypeSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=280)
    is_good_controlled = serializers.BooleanField()
    is_good_end_product = serializers.BooleanField()
    application = serializers.PrimaryKeyRelatedField(queryset=OpenApplication.objects.all())

    class Meta:
        model = GoodsType
        fields = ('id',
                  'description',
                  'is_good_controlled',
                  'control_code',
                  'is_good_end_product',
                  'application',
                  )

    def __init__(self, *args, **kwargs):
        """
        Initializes serializer for Goods Type
        """
        super(GoodsTypeSerializer, self).__init__(*args, **kwargs)

        # Only validate the control code if the good is controlled
        if str_to_bool(self.get_initial().get('is_good_controlled')) is True:
            self.fields['control_code'] = serializers.CharField(required=True)

    def update(self, instance, validated_data):
        """
        Update Goods Type Serializer
        """
        instance.description = validated_data.get('description', instance.description)
        instance.is_good_controlled = validated_data.get('is_good_controlled', instance.is_good_controlled)
        instance.control_code = validated_data.get('control_code', instance.control_code)
        instance.is_good_end_product = validated_data.get('is_good_end_product', instance.is_good_end_product)
        instance.save()
        return instance


class FullGoodsTypeSerializer(GoodsTypeSerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values('id', 'name'))

    class Meta:
        model = GoodsType
        fields = '__all__'
