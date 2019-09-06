from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from applications.models import Application
from conf.helpers import str_to_bool
from drafts.serializers import DraftBaseSerializer
from flags.enums import FlagStatuses
from goodstype.models import GoodsType


class BaseGoodsTypeSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=280)
    is_good_controlled = serializers.BooleanField()
    is_good_end_product = serializers.BooleanField()
    content_type = serializers.CharField()
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)

    def validate_content_type(self, value):
        return ContentType.objects.get(model=value)

    class Meta:
        model = GoodsType
        fields = ('id',
                  'description',
                  'is_good_controlled',
                  'control_code',
                  'is_good_end_product',
                  'content_type',
                  'content_type_name',
                  'object_id',
                  'content_object',
                  )

    def __init__(self, *args, **kwargs):
        """
        Initializes serializer for Goods Type
        """
        super(BaseGoodsTypeSerializer, self).__init__(*args, **kwargs)

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


class GoodsTypeSerializer(BaseGoodsTypeSerializer):
    content_object = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GoodsType
        fields = ('id',
                  'description',
                  'is_good_controlled',
                  'control_code',
                  'is_good_end_product',
                  'content_type',
                  'content_type_name',
                  'object_id',
                  'content_object',
                  )

    def get_content_object(self, instance):
        """
        Gets the content object of draft or application
        """
        from applications.serializers import ApplicationBaseSerializer
        if type(instance.content_object) == Application:
            return ApplicationBaseSerializer(instance.content_object).data
        return DraftBaseSerializer(instance.content_object).data


class FullGoodsTypeSerializer(BaseGoodsTypeSerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values('id', 'name'))

    class Meta:
        model = GoodsType
        fields = '__all__'
