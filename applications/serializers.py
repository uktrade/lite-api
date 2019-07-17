from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.enums import ApplicationLicenceType, ApplicationExportType, ApplicationStatus
from applications.libraries.get_application import get_application_by_pk
from applications.models import Application, GoodOnApplication, ApplicationDenialReason, CountryOnApplication, \
    ExternalLocationOnApplication
from applications.models import Site, SiteOnApplication
from end_user.models import EndUser
from end_user.serializers import EndUserSerializer
from goods.serializers import GoodSerializer
from organisations.models import ExternalLocation
from organisations.serializers import SiteViewSerializer, OrganisationViewSerializer, ExternalLocationSerializer
from static.countries.models import Country
from static.countries.serializers import CountrySerializer
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
                  'reason_details',
                  'reasons')


class ApplicationBaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    organisation = OrganisationViewSerializer()
    last_modified_at = serializers.DateTimeField(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    status = serializers.ChoiceField(choices=ApplicationStatus.choices)
    licence_type = serializers.ChoiceField(choices=ApplicationLicenceType.choices, error_messages={
        'required': 'Select which type of licence you want to apply for.'})
    export_type = serializers.ChoiceField(choices=ApplicationExportType.choices, error_messages={
        'required': 'Select if you want to apply for a temporary or permanent '
                    'licence.'})
    reference_number_on_information_form = serializers.CharField()
    application_denial_reason = ApplicationDenialReasonViewSerializer(read_only=True, many=True)

    # End User, Countries
    destinations = serializers.SerializerMethodField()

    # Sites, External Locations
    goods_locations = serializers.SerializerMethodField()

    def get_destinations(self, obj):
        countries_ids = CountryOnApplication.objects.filter(application=obj).values_list('country', flat=True)

        if obj.end_user:
            try:
                serializer = EndUserSerializer(obj.end_user)
                return {'type': 'end_user', 'data': serializer.data}
            except EndUser.DoesNotExist:
                return {'type': 'end_user', 'data': ''}
        else:
            countries = Country.objects.filter(id__in=countries_ids)
            serializer = CountrySerializer(countries, many=True)
            return {'type': 'countries', 'data': serializer.data}

    def get_goods_locations(self, obj):
        sites_on_application_ids = SiteOnApplication.objects.filter(application=obj)\
            .values_list('site', flat=True)
        sites = Site.objects.filter(id__in=sites_on_application_ids)
        external_locations_ids = ExternalLocationOnApplication.objects.filter(application=obj)\
            .values_list('external_location', flat=True)
        external_locations = ExternalLocation.objects.filter(id__in=external_locations_ids)

        if sites:
            serializer = SiteViewSerializer(sites, many=True)
            return {'type': 'sites', 'data': serializer.data}
        else:
            serializer = ExternalLocationSerializer(external_locations, many=True)
            return {'type': 'external_locations', 'data': serializer.data}

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
                  'application_denial_reason',
                  'destinations',
                  'goods_locations',)


class ApplicationDenialReasonSerializer(serializers.ModelSerializer):
    reason_details = serializers.CharField(max_length=2200, required=False, allow_blank=True, allow_null=True)
    application = serializers.PrimaryKeyRelatedField(queryset=Application.objects.all())

    class Meta:
        model = ApplicationDenialReason
        fields = ('reason_details',
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
    reasons = serializers.PrimaryKeyRelatedField(queryset=DenialReason.objects.all(), many=True, write_only=True)
    reason_details = serializers.CharField(required=False, allow_blank=True)

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
                  'reason_details',
                  'reference_number_on_information_form',)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the
        validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.activity = validated_data.get('activity', instance.activity)
        instance.usage = validated_data.get('usage', instance.usage)
        instance.status = validated_data.get('status', instance.status)
        instance.licence_type = validated_data.get('licence_type', instance.licence_type)
        instance.export_type = validated_data.get('export_type', instance.export_type)
        instance.reference_number_on_information_form = validated_data.get(
            'reference_number_on_information_form', instance.reference_number_on_information_form)


        # Remove any previous denial reasons
        if validated_data.get('status') == ApplicationStatus.APPROVED:
            ApplicationDenialReason.objects.filter(application=get_application_by_pk(instance.id)).delete()

        # If the status has been set to under final review, add reason_details to application
        if validated_data.get('status') == ApplicationStatus.UNDER_FINAL_REVIEW:
            data = {'application': instance.id,
                    'reason_details': validated_data.get('reason_details'),
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


class ApplicationCaseNotesSerializer(ApplicationBaseSerializer):
    case_notes = serializers.SerializerMethodField()

    def get_case_notes(self, obj):
        from cases.serializers import CaseNoteViewSerializer, CaseNote
        queryset = CaseNote.objects.filter(is_visible_to_exporter=True, case__application=obj)
        return CaseNoteViewSerializer(queryset, many=True).data

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
                  'application_denial_reason',
                  'destinations',
                  'goods_locations',
                  'case_notes')