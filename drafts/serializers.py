from rest_framework import serializers

from applications.serializers import GoodSerializer, DestinationSerializer
from drafts.models import Draft


class DraftBaseSerializer(serializers.ModelSerializer):
    destinations = DestinationSerializer(many=True, read_only=True)
    goods = GoodSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    last_modified_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    submitted_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)

    class Meta:
        model = Draft
        fields = ('id',
                  'user_id',
                  'name',
                  'activity',
                  'destination',
                  'usage',
                  'destinations',
                  'goods',
                  'created_at',
                  'last_modified_at',
                  'submitted_at')


class DraftCreateSerializer(DraftBaseSerializer):
    user_id = serializers.CharField()
    name = serializers.CharField()


class DraftUpdateSerializer(DraftBaseSerializer):
    name = serializers.CharField()
    usage = serializers.CharField()
    activity = serializers.CharField()
    destination = serializers.CharField()

    def update(self, instance, validated_data):
        """
        Update and return an existing `Draft` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.activity = validated_data.get('activity', instance.activity)
        instance.usage = validated_data.get('usage', instance.usage)
        instance.destination = validated_data.get('destination', instance.destination)
        instance.save()
        return instance




