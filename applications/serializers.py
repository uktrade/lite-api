from rest_framework import serializers
from enumchoicefield import EnumChoiceField

from applications.models import Application, ApplicationStatuses, GoodOnApplication
from goods.serializers import GoodSerializer


class GoodOnApplicationViewSerializer(serializers.ModelSerializer):
    good = GoodSerializer(read_only=True)

    class Meta:
        model = GoodOnApplication
        fields = ('id',
                  'good',
                  'quantity',
                  'unit',
                  'value')


class ApplicationBaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    last_modified_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    submitted_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = ('id',
                  'name',
                  'activity',
                  'destination',
                  'goods',
                  'usage',
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
    activity = serializers.CharField()
    destination = serializers.CharField()
    status = EnumChoiceField(enum_class=ApplicationStatuses)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.activity = validated_data.get('activity', instance.activity)
        instance.usage = validated_data.get('usage', instance.usage)
        instance.destination = validated_data.get('destination', instance.destination)
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance
