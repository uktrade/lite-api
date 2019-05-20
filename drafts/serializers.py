from enumchoicefield import EnumChoiceField
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from drafts.models import Draft, GoodOnDraft, LicenceType, ExportType
from goods.models import Good
from goods.serializers import GoodSerializer
from organisations.models import Organisation


class DraftBaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ', read_only=True)
    last_modified_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ', read_only=True)

    class Meta:
        model = Draft
        fields = ('id',
                  'name',
                  'activity',
                  'usage',
                  'organisation',
                  'created_at',
                  'last_modified_at',
                  'licence_type',
                  'export_type',
                  'reference_number_on_information_form',)


class DraftCreateSerializer(DraftBaseSerializer):
    name = serializers.CharField()
    licence_type = serializers.ChoiceField([(tag.name, tag.value) for tag in LicenceType])
    export_type = serializers.ChoiceField([(tag.name, tag.value) for tag in ExportType])
    reference_number_on_information_form = serializers.CharField(required=True, allow_blank=True)
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = Draft
        fields = ('id',
                  'name',
                  'licence_type',
                  'export_type',
                  'reference_number_on_information_form',
                  'organisation')


class DraftUpdateSerializer(DraftBaseSerializer):
    name = serializers.CharField()
    usage = serializers.CharField()
    activity = serializers.CharField()
    export_type = EnumChoiceField(enum_class=ExportType)
    reference_number_on_information_form = serializers.CharField()

    def update(self, instance, validated_data):
        """
        Update and return an existing `Draft` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.activity = validated_data.get('activity', instance.activity)
        instance.usage = validated_data.get('usage', instance.usage)
        instance.licence_type = validated_data.get('licence_type', instance.licence_type)
        instance.export_type = validated_data.get('export_type', instance.export_type)
        instance.reference_number_on_information_form = validated_data.get(
            'reference_number_on_information_form', instance.reference_number_on_information_form)
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
