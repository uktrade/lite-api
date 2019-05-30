from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.enums import ApplicationLicenceType, ApplicationExportType, ApplicationStatus
from applications.libraries.get_application import get_application_by_pk
from applications.models import Application, GoodOnApplication, ApplicationDenialReason
from applications.models import Site, SiteOnApplication
from goods.serializers import GoodSerializer
from organisations.serializers import SiteViewSerializer, OrganisationViewSerializer
from static.denial_reasons.models import DenialReason


class GoodOnApplicationViewSerializer(serializers.ModelSerializer):
    good = GoodSerializer(read_only=True)

    class Meta:
        model = GoodOnApplication
        fields = ('id',
                  'good',
                  'quantity',
                  'unit',
                  'value')


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
                  'reasoning',
                  'reasons')


class ApplicationBaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    organisation = OrganisationViewSerializer()
    last_modified_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    submitted_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    status = serializers.ChoiceField(choices=ApplicationStatus.choices)
    licence_type = serializers.ChoiceField(choices=ApplicationLicenceType.choices, error_messages={
        'required': 'Select which type of licence you want to apply for.'})
    export_type = serializers.ChoiceField(choices=ApplicationExportType.choices, error_messages={
        'required': 'Select if you want to apply for a temporary or permanent '
                    'licence.'})
    reference_number_on_information_form = serializers.CharField()
    application_denial_reason = ApplicationDenialReasonViewSerializer(read_only=True, many=True)

    class Meta:
        model = Application
        fields = ('id',
                  'name',
                  'organisation',
                  'activity',
                  'usage',
                  'goods',
                  'created_at',
                  'last_modified_at',
                  'submitted_at',
                  'status',
                  'licence_type',
                  'export_type',
                  'reference_number_on_information_form',
                  'application_denial_reason',)


class ApplicationDenialReasonSerializer(serializers.ModelSerializer):
    reasoning = serializers.CharField(max_length=2200, required=False, allow_blank=True, allow_null=True)
    application = serializers.PrimaryKeyRelatedField(queryset=Application.objects.all())

    class Meta:
        model = ApplicationDenialReason
        fields = ('reasoning',
                  'application')

    def create(self, validated_data):
        application_denial_reason = ApplicationDenialReason.objects.create(**validated_data)

        if self.initial_data['reasons']:
            for reason in self.initial_data['reasons']:
                application_denial_reason.reasons.add(reason)
        else:
            raise serializers.ValidationError('Select at least one denial reason')

        application_denial_reason.save()
        return application_denial_reason


class ApplicationUpdateSerializer(ApplicationBaseSerializer):
    name = serializers.CharField()
    usage = serializers.CharField()
    activity = serializers.CharField()
    status = serializers.ChoiceField(choices=ApplicationStatus.choices)
    licence_type = serializers.ChoiceField(choices=ApplicationLicenceType.choices, error_messages={
        'required': 'Select which type of licence you want to apply for.'})
    export_type = serializers.ChoiceField(choices=ApplicationExportType.choices, error_messages={
        'required': 'Select if you want to apply for a temporary or permanent '
                    'licence.'})
    reference_number_on_information_form = serializers.CharField()
    reasons = serializers.PrimaryKeyRelatedField(queryset=DenialReason.objects.all(), many=True, write_only=True)
    reasoning = serializers.CharField(required=False, allow_blank=True)


    def validate_reasons(self, attrs):
        if not attrs or len(attrs) == 0:
            raise serializers.ValidationError('Select at least one denial reason')
        return attrs

    class Meta:
        model = Application
        fields = ('id',
                  'name',
                  'organisation',
                  'activity',
                  'usage',
                  'goods',
                  'created_at',
                  'last_modified_at',
                  'submitted_at',
                  'status',
                  'licence_type',
                  'export_type',
                  'reasons',
                  'reasoning',
                  'reference_number_on_information_form',)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.activity = validated_data.get('activity', instance.activity)
        instance.usage = validated_data.get('usage', instance.usage)
        instance.status = validated_data.get('status', instance.status)
        instance.licence_type = validated_data.get('licence_type', instance.licence_type)
        instance.export_type = validated_data.get('export_type', instance.export_type)
        instance.reference_number_on_information_form = validated_data.get(
            'reference_number_on_information_form', instance.reference_number_on_information_form)

        # If the status has been set to under final review, add reasoning to application
        if validated_data.get('status') == ApplicationStatus.UNDER_FINAL_REVIEW:
            data = {'application': instance.id,
                    'reasoning': validated_data.get('reasoning'),
                    'reasons': validated_data.get('reasons')}

            application_denial_reason_serializer = ApplicationDenialReasonSerializer(data=data)
            if application_denial_reason_serializer.is_valid():
                # Delete existing ApplicationDenialReasons
                ApplicationDenialReason.objects.filter(application=get_application_by_pk(instance.id)).delete()

                # Create a new ApplicationDenialReasons
                application_denial_reason_serializer.save()
            else:
                raise serializers.ValidationError('An error occurred')

        instance.save()
        return instance


class SiteOnApplicationBaseSerializer(serializers.ModelSerializer):
    application = PrimaryKeyRelatedField(queryset=Application.objects.all())
    site = PrimaryKeyRelatedField(queryset=Site.objects.all())

    class Meta:
        model = SiteOnApplication
        fields = ('id',
                  'site',
                  'application')


class SiteOnApplicationViewSerializer(serializers.ModelSerializer):
    site = SiteViewSerializer(read_only=True, many=True)
    application = ApplicationBaseSerializer(read_only=True)

    class Meta:
        model = SiteOnApplication
        fields = ('id',
                  'site',
                  'application')
