from django.utils import timezone
from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.relations import PrimaryKeyRelatedField

from api.applications.enums import (
    ApplicationExportType,
    ApplicationExportLicenceOfficialType,
)
from api.applications.libraries.get_applications import get_application
from api.applications.models import BaseApplication, ApplicationDenialReason, ApplicationDocument
from api.applications.serializers.document import ApplicationDocumentSerializer
from cases.enums import CaseTypeSubTypeEnum
from cases.models import CaseType
from api.conf.helpers import get_value_from_enum
from api.conf.serializers import KeyValueChoiceField
from gov_users.serializers import GovUserSimpleSerializer
from lite_content.lite_api import strings
from api.organisations.models import Organisation, Site, ExternalLocation
from api.organisations.serializers import OrganisationDetailSerializer, ExternalLocationSerializer, SiteListSerializer
from api.parties.serializers import PartySerializer
from api.static.denial_reasons.models import DenialReason
from api.static.statuses.enums import CaseStatusEnum
from api.static.statuses.libraries.get_case_status import (
    get_status_value_from_case_status_enum,
    get_case_status_by_status,
)
from api.static.statuses.models import CaseStatus
from api.users.libraries.notifications import get_exporter_user_notification_individual_count
from api.users.models import ExporterUser


class TinyCaseTypeSerializer(serializers.ModelSerializer):
    sub_type = KeyValueChoiceField(choices=CaseTypeSubTypeEnum.choices)

    class Meta:
        model = CaseType
        fields = ("sub_type",)
        read_only_fields = fields


class GenericApplicationListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    case_type = TinyCaseTypeSerializer()
    status = serializers.SerializerMethodField()
    updated_at = serializers.DateTimeField()
    reference_code = serializers.CharField()
    export_type = serializers.SerializerMethodField()

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }

    def get_export_type(self, instance):
        if hasattr(instance, "export_type") and getattr(instance, "export_type"):
            return {
                "key": instance.export_type,
                "value": get_value_from_enum(instance.export_type, ApplicationExportType),
            }


class GenericApplicationViewSerializer(serializers.ModelSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Applications.Generic.MISSING_REFERENCE_NAME_ERROR},
    )
    case_type = serializers.SerializerMethodField()
    export_type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    organisation = OrganisationDetailSerializer()
    case = serializers.SerializerMethodField()
    exporter_user_notification_count = serializers.SerializerMethodField()
    is_major_editable = serializers.SerializerMethodField(required=False)
    goods_locations = serializers.SerializerMethodField()
    case_officer = GovUserSimpleSerializer()
    submitted_by = serializers.SerializerMethodField()

    class Meta:
        model = BaseApplication
        fields = (
            "id",
            "name",
            "organisation",
            "case_type",
            "export_type",
            "created_at",
            "updated_at",
            "submitted_at",
            "submitted_by",
            "status",
            "case",
            "exporter_user_notification_count",
            "reference_code",
            "is_major_editable",
            "goods_locations",
            "case_officer",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exporter_user = kwargs.get("context").get("exporter_user") if "context" in kwargs else None
        self.organisation_id = kwargs.get("context").get("organisation_id") if "context" in kwargs else None
        if not isinstance(self.exporter_user, ExporterUser):
            self.fields.pop("exporter_user_notification_count")

    def get_submitted_by(self, instance):
        return f"{instance.submitted_by.first_name} {instance.submitted_by.last_name}" if instance.submitted_by else ""

    def get_export_type(self, instance):
        instance = get_application(instance.pk)
        if hasattr(instance, "export_type"):
            return {
                "key": instance.export_type,
                "value": get_value_from_enum(instance.export_type, ApplicationExportType),
            }

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }

    def get_case_type(self, instance):
        from cases.serializers import CaseTypeSerializer

        return CaseTypeSerializer(instance.case_type).data

    def get_case(self, instance):
        return instance.pk

    def get_exporter_user_notification_count(self, instance):
        return get_exporter_user_notification_individual_count(
            exporter_user=self.exporter_user, organisation_id=self.organisation_id, case=instance,
        )

    def get_is_major_editable(self, instance):
        return instance.is_major_editable()

    def get_goods_locations(self, application):
        sites = Site.objects.filter(sites_on_application__application=application)
        if sites:
            serializer = SiteListSerializer(sites, many=True)
            return {"type": "sites", "data": serializer.data}

        external_locations = ExternalLocation.objects.filter(external_locations_on_application__application=application)
        if external_locations:
            serializer = ExternalLocationSerializer(external_locations, many=True)
            return {"type": "external_locations", "data": serializer.data}

        return {}

    def get_destinations(self, application):
        if getattr(application, "end_user", None):
            serializer = PartySerializer(application.end_user.party)
            return {"type": "end_user", "data": serializer.data}
        else:
            return {"type": "end_user", "data": ""}

    def get_additional_documents(self, instance):
        documents = ApplicationDocument.objects.filter(application=instance).order_by("created_at")
        return ApplicationDocumentSerializer(documents, many=True).data


class GenericApplicationCreateSerializer(serializers.ModelSerializer):
    def __init__(self, case_type_id, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["case_type"] = case_type_id
        self.initial_data["organisation"] = self.context.id

    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Applications.Generic.MISSING_REFERENCE_NAME_ERROR},
    )
    case_type = PrimaryKeyRelatedField(
        queryset=CaseType.objects.all(), error_messages={"required": strings.Applications.Generic.NO_LICENCE_TYPE},
    )
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = BaseApplication
        fields = (
            "id",
            "name",
            "case_type",
            "organisation",
        )

    def create(self, validated_data):
        validated_data["status"] = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return super().create(validated_data)


class GenericApplicationUpdateSerializer(serializers.ModelSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Applications.Generic.MISSING_REFERENCE_NAME_ERROR},
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
        instance.clearance_level = validated_data.get("clearance_level", instance.clearance_level)

        # Remove any previous denial reasons
        if validated_data.get("status") == get_case_status_by_status(CaseStatusEnum.FINALISED):
            ApplicationDenialReason.objects.filter(application=get_application(instance.id)).delete()
            instance.last_closed_at = timezone.now()

        instance = super().update(instance, validated_data)
        return instance


class GenericApplicationCopySerializer(serializers.ModelSerializer):
    """
    Serializer for copying applications that can handle any application type

    This is only used to verify the fields are correct that the user passes in, we then process the rest of the
     copy after validation
    """

    name = serializers.CharField(allow_null=False, allow_blank=False)
    have_you_been_informed = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    reference_number_on_information_form = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, max_length=255
    )

    class Meta:
        model = BaseApplication
        fields = (
            "name",
            "have_you_been_informed",
            "reference_number_on_information_form",
        )

    def __init__(self, context=None, *args, **kwargs):

        if context and context.get("application_type").sub_type == CaseTypeSubTypeEnum.STANDARD:
            self.fields["have_you_been_informed"] = KeyValueChoiceField(
                required=True,
                choices=ApplicationExportLicenceOfficialType.choices,
                error_messages={"required": strings.Goods.INFORMED},
            )
            if kwargs.get("data").get("have_you_been_informed") == ApplicationExportLicenceOfficialType.YES:
                self.fields["reference_number_on_information_form"] = serializers.CharField(
                    required=True, allow_blank=True, max_length=255
                )

        super().__init__(*args, **kwargs)
