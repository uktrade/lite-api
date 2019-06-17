from rest_framework import serializers

from conf.helpers import str_to_bool
from goodstype.models import GoodsType
from applications.models import Application
from applications.serializers import  ApplicationBaseSerializer
from drafts.serializers import DraftBaseSerializer


class GoodsTypeSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=280)
    is_good_controlled = serializers.BooleanField()
    is_good_end_product = serializers.BooleanField()
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    content_object = serializers.SerializerMethodField(read_only=True)

    def get_content_object(self, obj):

        if type(obj) == Application:
            return ApplicationBaseSerializer(obj.content_object).data
        return DraftBaseSerializer(obj.content_object).data

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
                  'content_object'
                  )

    def __init__(self, *args, **kwargs):
        super(GoodsTypeSerializer, self).__init__(*args, **kwargs)

        # Only validate the control code if the good is controlled
        if str_to_bool(self.get_initial().get('is_good_controlled')) is True:
            self.fields['control_code'] = serializers.CharField(required=True)

    def update(self, instance, validated_data):
        instance.description = validated_data.get('description', instance.description)
        instance.is_good_controlled = validated_data.get('is_good_controlled', instance.is_good_controlled)
        instance.control_code = validated_data.get('control_code', instance.control_code)
        instance.is_good_end_product = validated_data.get('is_good_end_product', instance.is_good_end_product)
        instance.save()
        return instance