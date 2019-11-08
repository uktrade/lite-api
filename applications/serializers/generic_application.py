from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.relations import PrimaryKeyRelatedField

from applications.enums import ApplicationType, ApplicationExportType, ApplicationExportLicenceOfficialType
from applications.libraries.get_applications import get_application
from applications.models import BaseApplication, ApplicationDenialReason
from applications.serializers.denial_reasons import ApplicationDenialReasonSerializer
from cases.models import Case
from conf.helpers import get_value_from_enum
from conf.serializers import KeyValueChoiceField
from content_strings.strings import get_string
from organisations.models import Organisation
from organisations.serializers import OrganisationDetailSerializer
from static.denial_reasons.models import DenialReason
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum, get_case_status_by_status
from static.statuses.models import CaseStatus


class GenericApplicationListSerializer(serializers.ModelSerializer):
    name = CharField(max_length=100,
                     required=True,
                     allow_blank=False,
                     allow_null=False,
                     error_messages={'blank': get_string('goods.error_messages.ref_name')})
    application_type = KeyValueChoiceField(choices=ApplicationType.choices)
    export_type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    organisation = OrganisationDetailSerializer()
    case = serializers.SerializerMethodField()

    def get_export_type(self, instance):
        instance = get_application(instance.pk)
        if hasattr(instance, 'export_type'):
            return {
                'key': instance.export_type,
                'value': get_value_from_enum(ApplicationExportType, instance.export_type)
            }
        return None

    def get_status(self, instance):
        if instance.status:
            return {
                'key': instance.status.status,
                'value': get_status_value_from_case_status_enum(instance.status.status)
            }
        return None

    def get_case(self, instance):
        try:
            return Case.objects.get(application=instance).id
        except Case.DoesNotExist:
            # Case will only exist if application has been submitted
            return None

    class Meta:
        model = BaseApplication
        fields = [
            'id',
            'name',
            'organisation',
            'application_type',
            'export_type',
            'created_at',
            'last_modified_at',
            'submitted_at',
            'status',
            'case',
        ]


class GenericApplicationCreateSerializer(serializers.ModelSerializer):
    name = CharField(max_length=100,
                     required=True,
                     allow_blank=False,
                     allow_null=False,
                     error_messages={'blank': get_string('goods.error_messages.ref_name')})
    application_type = KeyValueChoiceField(choices=ApplicationType.choices, error_messages={
        'required': get_string('applications.generic.no_licence_type')})
    export_type = KeyValueChoiceField(choices=ApplicationExportType.choices, error_messages={
        'required': get_string('applications.generic.no_export_type')})
    have_you_been_informed = KeyValueChoiceField(choices=ApplicationExportLicenceOfficialType.choices,
                                                 error_messages={
                                                     'required': get_string('goods.error_messages.informed')})
    reference_number_on_information_form = CharField(allow_blank=True)
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = BaseApplication
        fields = [
            'id',
            'name',
            'application_type',
            'export_type',
            'have_you_been_informed',
            'reference_number_on_information_form',
            'organisation',
        ]


class GenericApplicationUpdateSerializer(serializers.ModelSerializer):
    name = CharField(max_length=100,
                     required=True,
                     allow_blank=False,
                     allow_null=False,
                     error_messages={'blank': get_string('goods.error_messages.ref_name')})
    reasons = serializers.PrimaryKeyRelatedField(queryset=DenialReason.objects.all(), many=True, write_only=True)
    reason_details = serializers.CharField(required=False, allow_blank=True)
    status = serializers.PrimaryKeyRelatedField(queryset=CaseStatus.objects.all())

    class Meta:
        model = BaseApplication
        fields = [
            'name',
            'status',
            'reasons',
            'reason_details',
        ]

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.status = validated_data.get('status', instance.status)

        # Remove any previous denial reasons
        if validated_data.get('status') == get_case_status_by_status(CaseStatusEnum.FINALISED):
            ApplicationDenialReason.objects.filter(application=get_application(instance.id)).delete()

        # If the status has been set to under final review, add reason_details to application
        if validated_data.get('status') == get_case_status_by_status(CaseStatusEnum.UNDER_FINAL_REVIEW):
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
