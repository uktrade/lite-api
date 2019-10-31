from rest_framework import serializers

from applications.enums import ApplicationType
from applications.models import HmrcQuery
from conf.serializers import KeyValueChoiceField


class HmrcQueryViewSerializer(serializers.ModelSerializer):
    # application_type = KeyValueChoiceField(choices=ApplicationType.choices)

    class Meta:
        model = HmrcQuery
        fields = ['id', 'reasoning', 'application_type']


class HmrcQueryCreateSerializer(serializers.ModelSerializer):
    # application_type = KeyValueChoiceField(choices=ApplicationType.choices)

    class Meta:
        model = HmrcQuery
        fields = ['id', 'reasoning', 'application_type']


class HmrcQueryUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = HmrcQuery
        fields = ['reasoning']
