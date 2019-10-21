from datetime import datetime, timezone

from rest_framework import serializers
from rest_framework.fields import DecimalField, ChoiceField, CharField
from rest_framework.relations import PrimaryKeyRelatedField

from applications.enums import ApplicationLicenceType, ApplicationExportType, ApplicationExportLicenceOfficialType
from applications.libraries.get_applications import get_application
from applications.models import BaseApplication, GoodOnApplication, ApplicationDenialReason, StandardApplication, \
    OpenApplication, ApplicationDocument, ExternalLocationOnApplication
from applications.models import Site, SiteOnApplication
from cases.models import Case
from conf.serializers import KeyValueChoiceField
from content_strings.strings import get_string
from documents.libraries.process_document import process_document
from goods.models import Good
from goods.serializers import GoodWithFlagsSerializer, GoodSerializer
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
from organisations.models import ExternalLocation, Organisation
from organisations.serializers import SiteViewSerializer, ExternalLocationSerializer, OrganisationDetailSerializer
from parties.serializers import EndUserSerializer, UltimateEndUserSerializer, ConsigneeSerializer, ThirdPartySerializer
from static.countries.models import Country
from static.countries.serializers import CountrySerializer
from static.denial_reasons.models import DenialReason
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status_enum
from static.statuses.models import CaseStatus
from static.units.enums import Units


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


class BaseApplicationSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    organisation = OrganisationDetailSerializer()
    last_modified_at = serializers.DateTimeField(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)
    status = serializers.SerializerMethodField()
    licence_type = KeyValueChoiceField(choices=ApplicationLicenceType.choices, error_messages={
        'required': get_string('applications.generic.no_licence_type')})
    export_type = KeyValueChoiceField(choices=ApplicationExportType.choices, error_messages={
        'required': get_string('applications.generic.no_export_type')})
    reference_number_on_information_form = serializers.CharField()
    application_denial_reason = ApplicationDenialReasonViewSerializer(read_only=True, many=True)
    case = serializers.SerializerMethodField()

    additional_documents = serializers.SerializerMethodField()

    # Sites, External Locations
    goods_locations = serializers.SerializerMethodField()

    class Meta:
        model = BaseApplication
        fields = ('id',
                  'name',
                  'case',
                  'organisation',
                  'activity',
                  'usage',
                  'created_at',
                  'last_modified_at',
                  'submitted_at',
                  'status',
                  'licence_type',
                  'export_type',
                  'reference_number_on_information_form',
                  'application_denial_reason',
                  'goods_locations',
                  'additional_documents',)

    def get_additional_documents(self, instance):
        documents = ApplicationDocument.objects.filter(application=instance)
        return ApplicationDocumentSerializer(documents, many=True).data

    def get_case(self, instance):
        try:
            return Case.objects.get(application=instance).id
        except Case.DoesNotExist:
            # Case will only exist if application has been submitted
            return None

    def get_status(self, instance):
        return instance.status.status if instance.status else None

    def get_goods_locations(self, application):
        """
        An application, regardless of its type, has one goods location that will be either a site or an external
        location
        """
        sites = Site.objects.filter(sites_on_application__application=application)

        if sites:
            serializer = SiteViewSerializer(sites, many=True)
            return {'type': 'sites', 'data': serializer.data}

        external_locations = ExternalLocation.objects.filter(
            external_locations_on_application__application=application)

        if external_locations:
            serializer = ExternalLocationSerializer(external_locations, many=True)
            return {'type': 'external_locations', 'data': serializer.data}

        return {}


class StandardApplicationSerializer(BaseApplicationSerializer):
    end_user = EndUserSerializer()
    ultimate_end_users = UltimateEndUserSerializer(many=True)
    third_parties = ThirdPartySerializer(many=True)
    consignee = ConsigneeSerializer()
    goods = GoodOnApplicationWithFlagsViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()

    class Meta:
        model = StandardApplication
        fields = BaseApplicationSerializer.Meta.fields + (
            'end_user',
            'ultimate_end_users',
            'third_parties',
            'consignee',
            'goods',
            'destinations',)

    def get_destinations(self, application):
        if application.end_user:
            serializer = EndUserSerializer(application.end_user)
            return {'type': 'end_user', 'data': serializer.data}
        else:
            return {'type': 'end_user', 'data': ''}


class OpenApplicationSerializer(BaseApplicationSerializer):
    destinations = serializers.SerializerMethodField()
    goods_types = serializers.SerializerMethodField()

    class Meta:
        model = OpenApplication
        fields = BaseApplicationSerializer.Meta.fields + (
            'destinations',
            'goods_types',)

    def get_destinations(self, application):
        """
        For open applications, destinations are countries
        """
        countries = Country.objects.filter(countries_on_application__application=application)
        serializer = CountrySerializer(countries, many=True)
        return {'type': 'countries', 'data': serializer.data}

    def get_goods_types(self, application):
        goods_types = GoodsType.objects.filter(application=application)
        serializer = FullGoodsTypeSerializer(goods_types, many=True)
        return serializer.data


class ApplicationUpdateSerializer(BaseApplicationSerializer):
    class Meta:
        model = BaseApplication
        fields = ('name', 'reference_number_on_information_form', 'have_you_been_informed',)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.have_you_been_informed = validated_data.get('have_you_been_informed', instance.have_you_been_informed)
        instance.reference_number_on_information_form = validated_data.get(
            'reference_number_on_information_form', instance.reference_number_on_information_form)
        instance.last_modified_at = datetime.now(timezone.utc)
        instance.save()
        return instance


class ApplicationStatusUpdateSerializer(BaseApplicationSerializer):
    reasons = serializers.PrimaryKeyRelatedField(queryset=DenialReason.objects.all(), many=True, write_only=True)
    reason_details = serializers.CharField(required=False, allow_blank=True)
    status = serializers.PrimaryKeyRelatedField(queryset=CaseStatus.objects.all())

    class Meta:
        model = BaseApplication
        fields = ('status', 'reasons', 'reason_details',)

    def validate_reasons(self, attrs):
        if not attrs or len(attrs) == 0:
            raise serializers.ValidationError('Select at least one denial reason')
        return attrs

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the
        validated data.
        """
        instance.status = validated_data.get('status', instance.status)
        instance.last_modified_at = datetime.now(timezone.utc)

        # Remove any previous denial reasons
        if validated_data.get('status') == get_case_status_from_status_enum(CaseStatusEnum.FINALISED):
            ApplicationDenialReason.objects.filter(application=get_application(instance.id)).delete()

        # If the status has been set to under final review, add reason_details to application
        if validated_data.get('status') == get_case_status_from_status_enum(CaseStatusEnum.UNDER_FINAL_REVIEW):
            data = {'application': instance.id,
                    'reason_details': validated_data.get('reason_details'),
                    'reasons': validated_data.get('reasons')}

            application_denial_reason_serializer = ApplicationDenialReasonSerializer(data=data)
            if application_denial_reason_serializer.is_valid():
                # Delete existing ApplicationDenialReasons
                ApplicationDenialReason.objects.filter(
                    application=get_application(instance.id)).delete()

                # Create a new ApplicationDenialReason
                application_denial_reason_serializer.save()
            else:
                raise serializers.ValidationError('An error occurred')

        instance.save()
        return instance


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
    application = BaseApplicationSerializer(read_only=True)

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


class DraftApplicationCreateSerializer(serializers.ModelSerializer):
    name = CharField(max_length=100,
                     error_messages={'blank': get_string('goods.error_messages.ref_name')})
    licence_type = KeyValueChoiceField(choices=ApplicationLicenceType.choices, error_messages={
        'required': get_string('applications.generic.no_licence_type')})
    export_type = KeyValueChoiceField(choices=ApplicationExportType.choices, error_messages={
        'required': get_string('applications.generic.no_export_type')})
    have_you_been_informed = KeyValueChoiceField(choices=ApplicationExportLicenceOfficialType.choices,
                                                 error_messages={
                                                     'required': get_string('goods.error_messages.informed')})
    reference_number_on_information_form = CharField(required=True, allow_blank=True)
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = BaseApplication
        fields = ('id',
                  'name',
                  'licence_type',
                  'export_type',
                  'have_you_been_informed',
                  'reference_number_on_information_form',
                  'organisation',)
