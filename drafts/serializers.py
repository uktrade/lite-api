from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from drafts.models import Draft
from organisations.models import Organisation


class DraftBaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ', read_only=True)
    last_modified_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ', read_only=True)

    class Meta:
        model = Draft
        fields = ('id',
                  'name',
                  'activity',
                  'destination',
                  'usage',
                  'created_at',
                  'last_modified_at',)


class DraftCreateSerializer(DraftBaseSerializer):
    name = serializers.CharField()
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = Draft
        fields = ('id',
                  'name',
                  'organisation')


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


class GoodOnDraftBaseSerializer(serializers.ModelSerializer):
    good = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    application = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = GoodOnDraft
        fields = ('id',
                  'good',
                  'draft',
                  'quantity',
                  'unit',
                  'end_use_case',
                  'value')
