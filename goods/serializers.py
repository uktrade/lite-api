from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from clc_queries.models import ClcQuery
from clc_queries.enums import ClcQueryStatus
from goods.enums import GoodStatus, GoodControlled, GoodAreYouSure
from goods.models import Good
from organisations.models import Organisation


class GoodSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=280)
    is_good_controlled = serializers.ChoiceField(choices=GoodControlled.choices)
    control_code = serializers.CharField(required=False, default="", allow_blank=True)
    is_good_end_product = serializers.BooleanField()
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    status = serializers.ChoiceField(choices=GoodStatus.choices)
    not_sure_details_details = serializers.CharField(allow_blank=True, required=False)

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
                  'not_sure_details_details',
                  )

    def __init__(self, *args, **kwargs):
        super(GoodSerializer, self).__init__(*args, **kwargs)

    def validate(self, cleaned_data):
        is_controlled_good = cleaned_data.get('is_good_controlled') == GoodControlled.YES
        if is_controlled_good and not cleaned_data.get('control_code'):
            raise serializers.ValidationError('Control Code must be set when good is controlled')

        is_controlled_unsure = cleaned_data.get('is_good_controlled') == GoodControlled.UNSURE
        if is_controlled_unsure and not cleaned_data.get('not_sure_details_details'):
            raise serializers.ValidationError('Please enter details of why you don\'t know if your good is controlled')
        return cleaned_data

    def create(self, validated_data):
        not_sure_details_details = validated_data.pop('not_sure_details_details')

        good = super(GoodSerializer, self).create(validated_data)
        if not not_sure_details_details:
            ClcQuery.objects.create(good=good, details=not_sure_details_details, status=ClcQueryStatus.SUBMITTED)
        return good

    def update(self, instance, validated_data):
        instance.description = validated_data.get('description', instance.description)
        instance.is_good_controlled = validated_data.get('is_good_controlled', instance.is_good_controlled)
        instance.control_code = validated_data.get('control_code', instance.control_code)
        instance.is_good_end_product = validated_data.get('is_good_end_product', instance.is_good_end_product)
        instance.part_number = validated_data.get('part_number', instance.part_number)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance
