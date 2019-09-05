from rest_framework.fields import DateTimeField, CharField, ChoiceField, DecimalField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from applications.enums import ApplicationLicenceType, ApplicationExportType, ApplicationExportLicenceOfficialType
from conf.serializers import KeyValueChoiceField
from content_strings.strings import get_string
from drafts.models import Draft, GoodOnDraft, SiteOnDraft, ExternalLocationOnDraft
from parties.serializers import PartySerializer
from goods.models import Good
from goods.serializers import GoodSerializer
from organisations.models import Organisation, Site, ExternalLocation
from organisations.serializers import SiteViewSerializer
from static.units.enums import Units


class DraftBaseSerializer(ModelSerializer):
    licence_type = KeyValueChoiceField(choices=ApplicationLicenceType.choices, error_messages={
                                              'required': get_string('applications.generic.no_licence_type')})
    export_type = KeyValueChoiceField(choices=ApplicationExportType.choices, error_messages={
                                              'required': get_string('applications.generic.no_export_type')})
    created_at = DateTimeField(read_only=True)
    last_modified_at = DateTimeField(read_only=True)
    party = PartySerializer()

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
                  'have_you_been_informed',
                  'reference_number_on_information_form',
                  'parties')


class DraftCreateSerializer(DraftBaseSerializer):
    name = CharField(max_length=100,
                                 error_messages={'blank': get_string('goods.error_messages.ref_name')})
    licence_type = KeyValueChoiceField(choices=ApplicationLicenceType.choices, error_messages={
                                               'required': get_string('applications.generic.no_licence_type')})
    export_type = KeyValueChoiceField(choices=ApplicationExportType.choices, error_messages={
                                              'required': get_string('applications.generic.no_export_type')})
    have_you_been_informed = KeyValueChoiceField(choices=ApplicationExportLicenceOfficialType.choices,
                                                     error_messages={'required': get_string('goods.error_messages.informed')})
    reference_number_on_information_form = CharField(required=True, allow_blank=True)
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = Draft
        fields = ('id',
                  'name',
                  'licence_type',
                  'export_type',
                  'have_you_been_informed',
                  'reference_number_on_information_form',
                  'organisation')


class DraftUpdateSerializer(DraftBaseSerializer):
    name = CharField()
    usage = CharField()
    activity = CharField()
    export_type = KeyValueChoiceField(choices=ApplicationExportType.choices, error_messages={
                                              'required': get_string('applications.generic.no_export_type')})
    have_you_been_informed = ChoiceField(choices=ApplicationExportLicenceOfficialType.choices,
                                                     error_messages={'required': get_string('goods.error_messages.informed')})
    reference_number_on_information_form = CharField()

    def update(self, instance, validated_data):
        """
        Update and return an existing `Draft` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.activity = validated_data.get('activity', instance.activity)
        instance.usage = validated_data.get('usage', instance.usage)
        instance.licence_type = validated_data.get('licence_type', instance.licence_type)
        instance.export_type = validated_data.get('export_type', instance.export_type)
        instance.have_you_been_informed = validated_data.get('have_you_been_informed', instance.have_you_been_informed)
        instance.reference_number_on_information_form = validated_data.get(
            'reference_number_on_information_form', instance.reference_number_on_information_form)
        instance.save()
        return instance


class GoodOnDraftBaseSerializer(ModelSerializer):
    good = PrimaryKeyRelatedField(queryset=Good.objects.all())
    draft = PrimaryKeyRelatedField(queryset=Draft.objects.all())
    quantity = DecimalField(max_digits=256, decimal_places=6,
                                        error_messages={'invalid': get_string('goods.error_messages.invalid_qty')})
    value = DecimalField(max_digits=256, decimal_places=2,
                                     error_messages={'invalid': get_string('goods.error_messages.invalid_value')}),
    unit = ChoiceField(choices=Units.choices, error_messages={
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


class GoodOnDraftViewSerializer(ModelSerializer):
    good = GoodSerializer(read_only=True)
    unit = KeyValueChoiceField(choices=Units.choices)

    class Meta:
        model = GoodOnDraft
        fields = ('id',
                  'good',
                  'draft',
                  'quantity',
                  'unit',
                  'value')


class SiteOnDraftBaseSerializer(ModelSerializer):
    draft = PrimaryKeyRelatedField(queryset=Draft.objects.all())
    site = PrimaryKeyRelatedField(queryset=Site.objects.all())

    class Meta:
        model = SiteOnDraft
        fields = ('id',
                  'site',
                  'draft')


class SiteOnDraftViewSerializer(ModelSerializer):
    site = SiteViewSerializer(read_only=True)
    draft = DraftBaseSerializer(read_only=True)

    class Meta:
        model = SiteOnDraft
        fields = ('id',
                  'site',
                  'draft')


class ExternalLocationOnDraftSerializer(ModelSerializer):
    draft = PrimaryKeyRelatedField(queryset=Draft.objects.all())
    external_location = PrimaryKeyRelatedField(queryset=ExternalLocation.objects.all())

    class Meta:
        model = ExternalLocationOnDraft
        fields = ('id',
                  'external_location',
                  'draft')
