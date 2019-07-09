from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from clc_queries.models import ClcQuery
from goods.enums import GoodStatus, GoodControlled
from goods.models import Good
from organisations.models import Organisation
from cases.models import Case


class GoodSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=280)
    is_good_controlled = serializers.ChoiceField(choices=GoodControlled.choices)
    control_code = serializers.CharField(required=False, default="", allow_blank=True)
    is_good_end_product = serializers.BooleanField()
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    status = serializers.ChoiceField(choices=GoodStatus.choices)
    not_sure_details_details = serializers.CharField(allow_blank=True, required=False)
    clc_query_case_id = serializers.SerializerMethodField()

    class Meta:
        model = Good
        fields = ('id',
                  'description',
                  'is_good_controlled',
                  'clc_query_case_id',
                  'control_code',
                  'is_good_end_product',
                  'part_number',
                  'organisation',
                  'status',
                  'not_sure_details_details',
                  )

    def __init__(self, *args, **kwargs):
        super(GoodSerializer, self).__init__(*args, **kwargs)

        # Only validate the control code if the good is controlled
        if self.get_initial().get('is_good_controlled') == GoodControlled.YES:
            self.fields['control_code'] = serializers.CharField(required=True)

    # pylint: disable=W0703
    def get_clc_query_case_id(self, instance):
        try:
            clc_query = ClcQuery.objects.get(good=instance)
            case = Case.objects.get(clc_query=clc_query)
            return case.id
        except Exception:
            return None

    # pylint: disable=W0221
    def validate(self, value):
        is_controlled_good = value.get('is_good_controlled') == GoodControlled.YES
        if is_controlled_good and not value.get('control_code'):
            raise serializers.ValidationError('Control Code must be set when good is controlled')

        is_controlled_unsure = value.get('is_good_controlled') == GoodControlled.UNSURE
        if is_controlled_unsure and not value.get('not_sure_details_details'):
            raise serializers.ValidationError('Please enter details of why you don\'t know if your good is controlled')
        return value

    def create(self, validated_data):
        del validated_data['not_sure_details_details']

        good = super(GoodSerializer, self).create(validated_data)
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
