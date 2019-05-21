from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField
from enumchoicefield import ChoiceEnum, EnumChoiceField

from drafts.models import Draft, GoodOnDraft, SiteOnDraft
from goods.models import Good
from goods.serializers import GoodSerializer
from organisations.models import Organisation, Site
from organisations.serializers import SiteViewSerializer
from quantity.units import Units


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
                  'organisation',
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
    good = PrimaryKeyRelatedField(queryset=Good.objects.all())
    draft = PrimaryKeyRelatedField(queryset=Draft.objects.all())

    class Meta:
        model = GoodOnDraft
        fields = ('id',
                  'good',
                  'draft',
                  'quantity',
                  'unit',
                  'value')


class GoodOnDraftViewSerializer(serializers.ModelSerializer):
    good = GoodSerializer(read_only=True)
    unit = serializers.CharField()

    class Meta:
        model = GoodOnDraft
        fields = ('id',
                  'good',
                  'draft',
                  'quantity',
                  'unit',
                  'value')


class SiteOnDraftBaseSerializer(serializers.ModelSerializer):
    draft = PrimaryKeyRelatedField(queryset=Draft.objects.all())
    site = PrimaryKeyRelatedField(queryset=Site.objects.all())

    class Meta:
        model = SiteOnDraft
        fields = ('id',
                  'site',
                  'draft')


class SiteOnDraftViewSerializer(serializers.ModelSerializer):
    site = SiteViewSerializer(read_only=True)
    draft = DraftBaseSerializer(read_only=True)

    class Meta:
        model = SiteOnDraft
        fields = ('id',
                  'site',
                  'draft')
