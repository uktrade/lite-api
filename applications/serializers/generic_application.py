import abc

from applications.serializers.document import ApplicationDocumentSerializer
from lite_content.lite_api import strings
from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.relations import PrimaryKeyRelatedField

from applications.enums import (
    ApplicationType,
    ApplicationExportType,
    ApplicationExportLicenceOfficialType,
)
from applications.libraries.get_applications import get_application
from applications.models import BaseApplication, ApplicationDenialReason, ApplicationDocument
from conf.helpers import get_value_from_enum
from conf.serializers import KeyValueChoiceField
from organisations.models import Organisation, Site, ExternalLocation
from organisations.serializers import OrganisationDetailSerializer, SiteViewSerializer, ExternalLocationSerializer
from static.denial_reasons.models import DenialReason
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import (
    get_status_value_from_case_status_enum,
    get_case_status_by_status,
)
from static.statuses.models import CaseStatus
from users.libraries.notifications import (
    get_exporter_user_notifications_total_count,
    get_exporter_user_notifications_individual_counts,
)


class GenericApplicationListSerializer(serializers.ModelSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Goods.ErrorMessages.REF_NAME},
    )
    application_type = KeyValueChoiceField(choices=ApplicationType.choices)
    export_type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    organisation = OrganisationDetailSerializer()
    case = serializers.SerializerMethodField()
    exporter_user_notifications_count = serializers.SerializerMethodField()

    class Meta:
        model = BaseApplication
        fields = (
            "id",
            "name",
            "organisation",
            "application_type",
            "export_type",
            "created",
            "modified",
            "submitted_at",
            "status",
            "case",
            "exporter_user_notifications_count",
        )

    def get_export_type(self, instance):
        instance = get_application(instance.pk)
        if hasattr(instance, "export_type"):
            return {
                "key": instance.export_type,
                "value": get_value_from_enum(ApplicationExportType, instance.export_type),
            }
        return None

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None

    def get_case(self, instance):
        return instance.pk

    @abc.abstractmethod
    def get_exporter_user_notifications_count(self, instance):
        """
        This is used for list views only.
        To get the count for each type of notification on an application,
        override this function in child classes
        """

        return get_exporter_user_notifications_total_count(
            exporter_user=self.context.get("exporter_user"), case=instance
        )


class GenericApplicationViewSerializer(GenericApplicationListSerializer):
    # TODO: Rename to supporting_documentation when possible
    additional_documents = serializers.SerializerMethodField()
    goods_locations = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()

    class Meta:
        model = BaseApplication
        fields = GenericApplicationListSerializer.Meta.fields + (
            "additional_documents",
            "goods_locations",
            "destinations",
        )

    def get_exporter_user_notifications_count(self, instance):
        """
        Overriding parent class
        """

        return get_exporter_user_notifications_individual_counts(
            exporter_user=self.context.get("exporter_user"), case=instance
        )

    def get_additional_documents(self, instance):
        documents = ApplicationDocument.objects.filter(application=instance)
        return ApplicationDocumentSerializer(documents, many=True).data

    def get_goods_locations(self, application):
        sites = Site.objects.filter(sites_on_application__application=application)
        if sites:
            serializer = SiteViewSerializer(sites, many=True)
            return {"type": "sites", "data": serializer.data}

        external_locations = ExternalLocation.objects.filter(external_locations_on_application__application=application)
        if external_locations:
            serializer = ExternalLocationSerializer(external_locations, many=True)
            return {"type": "external_locations", "data": serializer.data}

        return {}

    @abc.abstractmethod
    def get_destinations(self, application):
        """
        Override this function in child classes
        """

        pass


class GenericApplicationCreateSerializer(serializers.ModelSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Goods.ErrorMessages.REF_NAME},
    )
    application_type = KeyValueChoiceField(
        choices=ApplicationType.choices, error_messages={"required": strings.Applications.Generic.NO_LICENCE_TYPE},
    )
    export_type = KeyValueChoiceField(
        choices=ApplicationExportType.choices, error_messages={"required": strings.Applications.Generic.NO_EXPORT_TYPE},
    )
    have_you_been_informed = KeyValueChoiceField(
        choices=ApplicationExportLicenceOfficialType.choices,
        error_messages={"required": strings.Goods.ErrorMessages.INFORMED},
    )
    reference_number_on_information_form = CharField(allow_blank=True)
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = BaseApplication
        fields = (
            "id",
            "name",
            "application_type",
            "export_type",
            "have_you_been_informed",
            "reference_number_on_information_form",
            "organisation",
            "status",
        )


class GenericApplicationUpdateSerializer(serializers.ModelSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Goods.ErrorMessages.REF_NAME},
    )
    reasons = serializers.PrimaryKeyRelatedField(queryset=DenialReason.objects.all(), many=True, write_only=True)
    reason_details = serializers.CharField(required=False, allow_blank=True)
    status = serializers.PrimaryKeyRelatedField(queryset=CaseStatus.objects.all())

    class Meta:
        model = BaseApplication
        fields = (
            "name",
            "status",
            "reasons",
            "reason_details",
        )

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the validated data.
        """
        instance.name = validated_data.get("name", instance.name)
        instance.status = validated_data.get("status", instance.status)

        # Remove any previous denial reasons
        if validated_data.get("status") == get_case_status_by_status(CaseStatusEnum.FINALISED):
            ApplicationDenialReason.objects.filter(application=get_application(instance.id)).delete()

        instance.save()
        return instance
