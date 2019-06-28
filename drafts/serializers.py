from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.enums import ApplicationLicenceType, ApplicationExportType
from content_strings.strings import get_string
from drafts.models import Draft, GoodOnDraft, SiteOnDraft, ExternalLocationOnDraft
from end_user.serializers import EndUserSerializer
from goods.enums import GoodStatus
from goods.models import Good
from goods.serializers import GoodSerializer
from organisations.models import Organisation, Site, ExternalLocation
from organisations.serializers import SiteViewSerializer


class DraftBaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    last_modified_at = serializers.DateTimeField(read_only=True)
    end_user = EndUserSerializer()

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
                  'reference_number_on_information_form',
                  'end_user')


class DraftCreateSerializer(DraftBaseSerializer):
    name = serializers.CharField(max_length=100,
                                 error_messages={'blank': 'Enter a reference name for your application.'})
    licence_type = serializers.ChoiceField(choices=ApplicationLicenceType.choices, error_messages={
        'required': 'Select which type of licence you want to apply for.'})
    export_type = serializers.ChoiceField(choices=ApplicationExportType.choices, error_messages={
        'required': 'Select if you want to apply for a temporary or permanent '
                    'licence.'})
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
    export_type = serializers.ChoiceField(choices=ApplicationExportType.choices, error_messages={
        'required': 'Select if you want to apply for a temporary or permanent '
                    'licence.'})
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
    quantity = serializers.DecimalField(max_digits=256, decimal_places=6,
                                        error_messages={'invalid': 'Enter a valid quantity'})
    value = serializers.DecimalField(max_digits=256, decimal_places=2,
                                     error_messages={'invalid': 'Enter a valid value'})
    unit = serializers.ChoiceField(choices=GoodStatus.choices, error_messages={
        'required': get_string('goods.error_messages.required_unit'),
        'invalid_choice': get_string('goods.error_messages.required_unit')})

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


class ExternalLocationOnDraftSerializer(serializers.ModelSerializer):
    draft = PrimaryKeyRelatedField(queryset=Draft.objects.all())
    external_location = PrimaryKeyRelatedField(queryset=ExternalLocation.objects.all())

    class Meta:
        model = ExternalLocationOnDraft
        fields = ('id',
                  'external_location',
                  'draft')
