from rest_framework import serializers
from enumchoicefield import EnumChoiceField

from applications.models import Application, ApplicationStatuses, Destination, Good


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ('id', 'name')


class GoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = ('id', 'name', 'description', 'quantity', 'control_code')


class ApplicationBaseSerializer(serializers.ModelSerializer):
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
                  'submitted_at',
                  'status')


class ApplicationCreateSerializer(ApplicationBaseSerializer):
    user_id = serializers.CharField()
    name = serializers.CharField()


class ApplicationUpdateSerializer(ApplicationBaseSerializer):
    name = serializers.CharField()
    usage = serializers.CharField()
    control_code = serializers.CharField()
    activity = serializers.CharField()
    destination = serializers.CharField()
    status = EnumChoiceField(enum_class=ApplicationStatuses)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.control_code = validated_data.get('control_code', instance.control_code)
        instance.activity = validated_data.get('activity', instance.activity)
        instance.usage = validated_data.get('usage', instance.usage)
        instance.destination = validated_data.get('destination', instance.destination)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance
