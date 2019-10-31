from rest_framework import serializers
from rest_framework.fields import DecimalField, ChoiceField
from rest_framework.relations import PrimaryKeyRelatedField

from applications.models import BaseApplication, SiteOnApplication, ExternalLocationOnApplication, StandardApplication, \
    GoodOnApplication, ApplicationDenialReason, ApplicationDocument
from conf.serializers import KeyValueChoiceField
from content_strings.strings import get_string
from documents.libraries.process_document import process_document
from goods.models import Good
from goods.serializers import GoodWithFlagsSerializer, GoodSerializer
from organisations.models import Site, ExternalLocation
from organisations.serializers import SiteViewSerializer
from static.denial_reasons.models import DenialReason
from static.units.enums import Units


class SiteOnApplicationCreateSerializer(serializers.ModelSerializer):
    application = PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    site = PrimaryKeyRelatedField(queryset=Site.objects.all())

    class Meta:
        model = SiteOnApplication
        fields = ('id',
                  'site',
                  'application',)


class SiteOnApplicationViewSerializer(serializers.ModelSerializer):
    site = SiteViewSerializer(read_only=True, many=True)
    # application = BaseApplicationSerializer(read_only=True)

    class Meta:
        model = SiteOnApplication
        fields = ('id',
                  'site',
                  'application',)


class ExternalLocationOnApplicationSerializer(serializers.ModelSerializer):
    application = PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    external_location = PrimaryKeyRelatedField(queryset=ExternalLocation.objects.all())

    class Meta:
        model = ExternalLocationOnApplication
        fields = ('id',
                  'external_location',
                  'application',)


class GoodOnApplicationWithFlagsViewSerializer(serializers.ModelSerializer):
    good = GoodWithFlagsSerializer(read_only=True)
    unit = KeyValueChoiceField(choices=Units.choices)

    class Meta:
        model = GoodOnApplication
        fields = ('id',
                  'good',
                  'quantity',
                  'unit',
                  'value',)


class GoodOnApplicationViewSerializer(serializers.ModelSerializer):
    good = GoodSerializer(read_only=True)
    unit = KeyValueChoiceField(choices=Units.choices)

    class Meta:
        model = GoodOnApplication
        fields = ('id',
                  'good',
                  'application',
                  'quantity',
                  'unit',
                  'value',)


class GoodOnApplicationCreateSerializer(serializers.ModelSerializer):
    good = PrimaryKeyRelatedField(queryset=Good.objects.all())
    application = PrimaryKeyRelatedField(queryset=StandardApplication.objects.all())
    quantity = DecimalField(max_digits=256, decimal_places=6,
                            error_messages={'invalid': get_string('goods.error_messages.invalid_qty')})
    value = DecimalField(max_digits=256, decimal_places=2,
                         error_messages={'invalid': get_string('goods.error_messages.invalid_value')}),
    unit = ChoiceField(choices=Units.choices, error_messages={
        'required': get_string('goods.error_messages.required_unit'),
        'invalid_choice': get_string('goods.error_messages.required_unit')})

    class Meta:
        model = GoodOnApplication
        fields = ('id',
                  'good',
                  'application',
                  'quantity',
                  'unit',
                  'value',)


class DenialReasonSerializer(serializers.ModelSerializer):
    id = serializers.CharField()

    class Meta:
        model = DenialReason
        fields = ('id',)


class ApplicationDenialReasonViewSerializer(serializers.ModelSerializer):
    reasons = DenialReasonSerializer(read_only=False, many=True)

    class Meta:
        model = ApplicationDenialReason
        fields = ('id',
                  'reason_details',
                  'reasons',)


class ApplicationDenialReasonSerializer(serializers.ModelSerializer):
    reason_details = serializers.CharField(max_length=2200, required=False, allow_blank=True, allow_null=True)
    application = serializers.PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())

    class Meta:
        model = ApplicationDenialReason
        fields = ('reason_details',
                  'application',)

    def create(self, validated_data):
        if self.initial_data['reasons']:
            application_denial_reason = ApplicationDenialReason.objects.create(**validated_data)
            application_denial_reason.reasons.set(self.initial_data['reasons'])
            application_denial_reason.save()

            return application_denial_reason
        else:
            raise serializers.ValidationError('Select at least one denial reason')


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationDocument
        fields = '__all__'

    def create(self, validated_data):
        document = super(ApplicationDocumentSerializer, self).create(validated_data)
        document.save()
        process_document(document)
        return document
