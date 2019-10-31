from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.relations import PrimaryKeyRelatedField

from applications.enums import ApplicationType, ApplicationExportType, ApplicationExportLicenceOfficialType
from applications.libraries.get_applications import get_application
from applications.models import BaseApplication, ApplicationDenialReason
from applications.serializers.other import ApplicationDenialReasonSerializer
from conf.serializers import KeyValueChoiceField
from content_strings.strings import get_string
from organisations.models import Organisation
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum, get_case_status_by_status


class GenericApplicationListSerializer(serializers.ModelSerializer):
    application_type = KeyValueChoiceField(choices=ApplicationType.choices)
    export_type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_export_type(self, instance):
        instance = get_application(instance.pk)
        if hasattr(instance, 'export_type'):
            return {
                'key': instance.export_type,
                'value': instance.export_type,
            }

        return None

    def get_status(self, instance):
        status = instance.status.status if instance.status else None
        return {
            'key': status,
            'value': get_status_value_from_case_status_enum(status) if status else None
        }

    class Meta:
        model = BaseApplication
        fields = ['name',
                  'application_type',
                  'export_type',
                  'created_at',
                  'last_modified_at',
                  'submitted_at',
                  'status']


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
        fields = ('id',
                  'name',
                  'application_type',
                  'export_type',
                  'have_you_been_informed',
                  'reference_number_on_information_form',
                  'organisation',)


class GenericApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseApplication
        fields = ['name',
                  'reference_number_on_information_form',
                  'status',]

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.reference_number_on_information_form = \
            validated_data.get('reference_number_on_information_form', instance.name)
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


# class BaseApplicationSerializer(serializers.ModelSerializer):
#     created_at = serializers.DateTimeField(read_only=True)
#     organisation = OrganisationDetailSerializer()
#     last_modified_at = serializers.DateTimeField(read_only=True)
#     submitted_at = serializers.DateTimeField(read_only=True)
#     status = serializers.SerializerMethodField()
#     application_type = KeyValueChoiceField(choices=ApplicationType.choices, error_messages={
#         'required': get_string('applications.generic.no_licence_type')})
#     application_denial_reason = ApplicationDenialReasonViewSerializer(read_only=True, many=True)
#     case = serializers.SerializerMethodField()
#
#     additional_documents = serializers.SerializerMethodField()
#
#     # Sites, External Locations
#     goods_locations = serializers.SerializerMethodField()
#
#     class Meta:
#         model = BaseApplication
#         fields = ('id',
#                   'name',
#                   'case',
#                   'organisation',
#                   'activity',
#                   'usage',
#                   'created_at',
#                   'last_modified_at',
#                   'submitted_at',
#                   'status',
#                   'application_type',
#                   'export_type',
#                   'have_you_been_informed',
#                   'reference_number_on_information_form',
#                   'application_denial_reason',
#                   'goods_locations',
#                   'additional_documents',)
#
#     def get_additional_documents(self, instance):
#         documents = ApplicationDocument.objects.filter(application=instance)
#         return ApplicationDocumentSerializer(documents, many=True).data
#
#     def get_case(self, instance):
#         try:
#             return Case.objects.get(application=instance).id
#         except Case.DoesNotExist:
#             # Case will only exist if application has been submitted
#             return None
#
#     def get_status(self, instance):
#         status = instance.status.status if instance.status else None
#         return {
#             'key': status,
#             'value': get_status_value_from_case_status_enum(status) if status else None
#         }
#
#     def get_goods_locations(self, application):
#         """
#         An application, regardless of its type, has one goods location that will be either a site or an external
#         location
#         """
#         sites = Site.objects.filter(sites_on_application__application=application)
#
#         if sites:
#             serializer = SiteViewSerializer(sites, many=True)
#             return {'type': 'sites', 'data': serializer.data}
#
#         external_locations = ExternalLocation.objects.filter(
#             external_locations_on_application__application=application)
#
#         if external_locations:
#             serializer = ExternalLocationSerializer(external_locations, many=True)
#             return {'type': 'external_locations', 'data': serializer.data}
#
#         return {}
