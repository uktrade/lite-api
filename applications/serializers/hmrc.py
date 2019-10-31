from rest_framework import serializers

from applications.models import HmrcQuery


class HmrcQueryViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = HmrcQuery
        fields = ['id', 'reasoning', 'application_type']


class HmrcQueryUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = HmrcQuery
        fields = ['reasoning']
