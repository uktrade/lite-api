from rest_framework import serializers
from drafts.models import Drafts

"""
This file contains the Serializer Classes which are used derive serializers for Drafts and Applications
"""


class CommonBaseSerializer(serializers.ModelSerializer):
    destinations = DestinationSerializer(many=True, read_only=True)
    goods = GoodSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    last_modified_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    submitted_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)

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


class CommonCreateSerializer(CommonBaseSerializer):
    user_id = serializers.CharField()
    name = serializers.CharField()


class CommonUpdateSerializer(CommonBaseSerializer):
    name = serializers.CharField()
    usage = serializers.CharField()
    control_code = serializers.CharField()
    activity = serializers.CharField()
    destination = serializers.CharField()
