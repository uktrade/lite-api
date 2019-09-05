from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.enums import ApplicationLicenceType, ApplicationExportType
from applications.libraries.get_application import get_application_by_pk
from applications.libraries.get_ultimate_end_users import get_ultimate_end_users
from applications.models import Application, GoodOnApplication, ApplicationDenialReason, CountryOnApplication, \
    ExternalLocationOnApplication
from applications.models import Site, SiteOnApplication
from cases.libraries.get_case_note import get_case_notes_from_case
from cases.models import Case
from conf.serializers import KeyValueChoiceField
from content_strings.strings import get_string
from parties.models import Party
from parties.serializers import PartySerializer
from goods.serializers import GoodSerializer
from goodstype.models import GoodsType
from goodstype.serializers import GoodsTypeSerializer
from organisations.models import ExternalLocation
from organisations.serializers import SiteViewSerializer, OrganisationViewSerializer, ExternalLocationSerializer
from static.countries.models import Country
from static.countries.serializers import CountrySerializer
from static.denial_reasons.models import DenialReason
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status
from static.statuses.models import CaseStatus
from static.units.enums import Units


class GoodOnApplicationViewSerializer(serializers.ModelSerializer):
    good = GoodSerializer(read_only=True)
    unit = KeyValueChoiceField(choices=Units.choices)

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
    status = serializers.SerializerMethodField()
    licence_type = KeyValueChoiceField(choices=ApplicationLicenceType.choices, error_messages={
        'required': get_string('applications.generic.no_licence_type')})
    export_type = KeyValueChoiceField(choices=ApplicationExportType.choices, error_messages={
        'required': get_string('applications.generic.no_export_type')})
    reference_number_on_information_form = serializers.CharField()
    application_denial_reason = ApplicationDenialReasonViewSerializer(read_only=True, many=True)

    # Goods
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    goods_types = serializers.SerializerMethodField()

    # End User, Countries
    destinations = serializers.SerializerMethodField()

    # Ultimate End Users
    ultimate_end_users = serializers.SerializerMethodField()

    # Sites, External Locations
    goods_locations = serializers.SerializerMethodField()

    case = serializers.SerializerMethodField()

    def get_case(self, instance):
        return Case.objects.get(application=instance).id

    # pylint: disable=W0221
    def get_status(self, instance):
        return instance.status.status

    def get_goods_types(self, application):
        goods_types = GoodsType.objects.filter(object_id=application.id)
        serializer = GoodsTypeSerializer(goods_types, many=True)
        return serializer.data

    def get_destinations(self, application):
        countries_ids = CountryOnApplication.objects.filter(application=application).values_list('country', flat=True)
        party = Party.objects.get(application=application)
        if party.application:
            try:
                serializer = PartySerializer(application.party)
                return {'type': 'parties', 'data': serializer.data}
            except Party.DoesNotExist:
                return {'type': 'parties', 'data': ''}
        else:
            countries = Country.objects.filter(id__in=countries_ids)
            serializer = CountrySerializer(countries, many=True)
            return {'type': 'countries', 'data': serializer.data}

    def get_ultimate_end_users(self, application):
        ultimate_end_users = get_ultimate_end_users(application)
        serializer = PartySerializer(ultimate_end_users, many=True)
        return serializer.data

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
                  'case',
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
                  'ultimate_end_users',
                  'goods_locations',
                  'goods_types')


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
    status = serializers.PrimaryKeyRelatedField(queryset=CaseStatus.objects.all())

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
        if validated_data.get('status') == get_case_status_from_status(CaseStatusEnum.APPROVED):
            ApplicationDenialReason.objects.filter(application=get_application_by_pk(instance.id)).delete()

        # If the status has been set to under final review, add reason_details to application
        if validated_data.get('status') == get_case_status_from_status(CaseStatusEnum.UNDER_FINAL_REVIEW):
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


class SiteOnApplicationCreateSerializer(serializers.ModelSerializer):
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
    case = serializers.SerializerMethodField()
    case_notes = serializers.SerializerMethodField()

    def get_case_notes(self, obj):
        from cases.serializers import CaseNoteSerializer
        data = get_case_notes_from_case(Case.objects.get(application=obj.id), True)
        return CaseNoteSerializer(data, many=True).data

    # pylint: disable=W0221
    def get_status(self, instance):
        return instance.status.status

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
                  'case_notes',
                  'case')
