from rest_framework import serializers
from applications.models import Application, Destination, Good


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ('id', 'name')


class GoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = ('id', 'name', 'description', 'quantity', 'control_code')


class ApplicationSerializer(serializers.ModelSerializer):
    destinations = DestinationSerializer(many=True, read_only=True)
    goods = GoodSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    last_modified_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    submitted_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")

    class Meta:
        model = Application
        fields = ('id',
                  'user_id',
                  'name',
                  'control_code',
                  'activity',
                  'destination',
                  'usage',
                  'destinations',
                  'goods',
                  'created_at',
                  'last_modified_at',
                  'submitted_at')
