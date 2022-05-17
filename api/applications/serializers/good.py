from rest_framework import serializers
from rest_framework.fields import DecimalField, ChoiceField, BooleanField
from rest_framework.relations import PrimaryKeyRelatedField

from django.forms.models import model_to_dict

from api.applications.models import (
    GoodOnApplicationDocument,
    GoodOnApplicationInternalDocument,
    BaseApplication,
    GoodOnApplication,
    GoodOnApplicationControlListEntry,
)
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.audit_trail.serializers import AuditSerializer
from api.cases.enums import CaseTypeEnum
from api.cases.models import Case
from api.core.serializers import KeyValueChoiceField
from api.documents.libraries.process_document import process_document
from api.goods.enums import GoodControlled, ItemType
from api.goods.helpers import update_firearms_certificate_data
from api.goods.models import Good
from api.goods.serializers import GoodSerializerInternal, FirearmDetailsSerializer
from api.licences.models import GoodOnLicence
from api.organisations.models import DocumentOnOrganisation
from api.staticdata.control_list_entries.serializers import ControlListEntrySerializer
from api.staticdata.units.enums import Units
from api.users.models import ExporterUser
from api.users.serializers import ExporterUserSimpleSerializer
from lite_content.lite_api import strings


class GoodOnStandardLicenceSerializer(serializers.ModelSerializer):
    quantity = serializers.FloatField(
        required=True,
        allow_null=False,
        min_value=0,
        error_messages={
            "null": strings.Licence.NULL_QUANTITY_ERROR,
            "min_value": strings.Licence.NEGATIVE_QUANTITY_ERROR,
        },
    )
    value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=True,
        allow_null=False,
        min_value=0,
        error_messages={
            "null": strings.Licence.NULL_VALUE_ERROR,
            "min_value": strings.Licence.NEGATIVE_VALUE_ERROR,
        },
    )

    class Meta:
        model = GoodOnLicence
        fields = (
            "id",
            "quantity",
            "value",
            "good",
            "licence",
        )

    def validate(self, data):
        if data["quantity"] > self.context.get("applied_for_quantity"):
            raise serializers.ValidationError({"quantity": strings.Licence.INVALID_QUANTITY_ERROR})
        return data


class GoodOnApplicationControlListEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodOnApplicationControlListEntry
        fields = "__all__"


class GoodOnApplicationViewSerializer(serializers.ModelSerializer):
    good = GoodSerializerInternal(read_only=True)
    good_application_documents = serializers.SerializerMethodField()
    good_application_internal_documents = serializers.SerializerMethodField()
    unit = KeyValueChoiceField(choices=Units.choices)
    flags = serializers.SerializerMethodField()
    control_list_entries = ControlListEntrySerializer(many=True)
    audit_trail = serializers.SerializerMethodField()
    is_good_controlled = KeyValueChoiceField(choices=GoodControlled.choices)
    firearm_details = FirearmDetailsSerializer()

    class Meta:
        model = GoodOnApplication
        fields = (
            "id",
            "created_at",
            "updated_at",
            "good",
            "application",
            "quantity",
            "unit",
            "value",
            "is_good_incorporated",
            "flags",
            "item_type",
            "other_item_type",
            "is_good_controlled",
            "control_list_entries",
            "end_use_control",
            "comment",
            "report_summary",
            "audit_trail",
            "firearm_details",
            "good_application_documents",
            "good_application_internal_documents",
            "is_precedent",
        )

    def get_flags(self, instance):
        return list(instance.good.flags.values("id", "name", "colour", "label"))

    def get_good_application_documents(self, instance):
        documents = GoodOnApplicationDocument.objects.filter(
            application=instance.application, good=instance.good, safe=True
        )
        return GoodOnApplicationDocumentViewSerializer(documents, many=True).data

    def get_good_application_internal_documents(self, instance):
        documents = GoodOnApplicationInternalDocument.objects.filter(good_on_application=instance.id, safe=True)
        return GoodOnApplicationInternalDocumentViewSerializer(documents, many=True).data

    def get_audit_trail(self, instance):
        # this serializer is used by a few views. Most views do not need to know audit trail
        if not self.context.get("include_audit_trail"):
            return []
        return AuditSerializer(instance.audit_trail.all(), many=True).data

    def update(self, instance, validated_data):
        if "firearm_details" in validated_data:
            firearm_details_serializer = self.fields["firearm_details"]
            firearm_details_validated_data = validated_data.pop("firearm_details")
            firearm_details_serializer.update(instance.firearm_details, firearm_details_validated_data)

        return super().update(instance, validated_data)


class GoodOnApplicationCreateSerializer(serializers.ModelSerializer):
    good = PrimaryKeyRelatedField(queryset=Good.objects.all())
    application = PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    value = DecimalField(max_digits=15, decimal_places=2, error_messages={"invalid": strings.Goods.INVALID_VALUE})
    quantity = DecimalField(max_digits=15, decimal_places=6, error_messages={"invalid": strings.Goods.INVALID_QUANTITY})
    unit = ChoiceField(
        choices=Units.choices,
        error_messages={"required": strings.Goods.REQUIRED_UNIT, "invalid_choice": strings.Goods.REQUIRED_UNIT},
    )
    is_good_incorporated = BooleanField(required=True, error_messages={"required": strings.Goods.INCORPORATED_ERROR})
    item_type = serializers.ChoiceField(choices=ItemType.choices, error_messages={"required": strings.Goods.ITEM_TYPE})
    other_item_type = serializers.CharField(
        max_length=100,
        error_messages={"required": strings.Goods.OTHER_ITEM_TYPE, "blank": strings.Goods.OTHER_ITEM_TYPE},
    )
    firearm_details = FirearmDetailsSerializer(required=False)

    class Meta:
        model = GoodOnApplication
        fields = (
            "id",
            "good",
            "application",
            "value",
            "quantity",
            "unit",
            "is_good_incorporated",
            "item_type",
            "other_item_type",
            "firearm_details",
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        data = self.initial_data
        case_type = Case.objects.get(id=data["application"]).case_type
        # Exbition queries do not have the typical data for goods on applications that other goods do
        #  as a result, we have to set them as false when not required and vice versa for other applications
        if case_type.id == CaseTypeEnum.EXHIBITION.id:
            self.fields["value"].required = False
            self.fields["quantity"].required = False
            self.fields["unit"].required = False
            self.fields["is_good_incorporated"].required = False
            # If the user passes item_type forward as anything but other, we do not want to store "other_item_type"
            if not data.get("item_type") == ItemType.OTHER:
                if isinstance(data.get("other_item_type"), str):
                    del data["other_item_type"]
                self.fields["other_item_type"].required = False
        else:
            self.fields["item_type"].required = False
            self.fields["other_item_type"].required = False

            if data.get("unit") == Units.ITG:
                # If the good is intangible, the value and quantity become optional
                self.fields["value"].required = False
                self.fields["quantity"].required = False

                # If the quantity or value aren't set, they are defaulted to 1 and 0 respectively
                if not data["quantity"]:
                    data["quantity"] = 1
                    if data.get("firearm_details"):
                        data["firearm_details"]["number_of_items"] = 1
                if not data["value"]:
                    data["value"] = 0

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as error:
            if "firearm_details" in error.detail:
                raise serializers.ValidationError(error.detail["firearm_details"])
            raise

    def create(self, validated_data):
        if validated_data.get("firearm_details"):
            # copy the data from the "firearm detail on good" level to "firearm detail on good-on-application" level
            firearm_data = model_to_dict(validated_data["good"].firearm_details)
            # since in the instance no manufacture date is set it retrieves as null. This is requires to avoid a
            # validation error as this is an optional question when saving against a good application
            if "year_of_manufacture" in firearm_data and firearm_data["year_of_manufacture"] is None:
                del firearm_data["year_of_manufacture"]
            if validated_data.get("firearm_details"):
                firearm_data.update(validated_data["firearm_details"])
            firearm_data = update_firearms_certificate_data(validated_data["good"].organisation_id, firearm_data)
            serializer = FirearmDetailsSerializer(data=firearm_data)
            serializer.is_valid(raise_exception=True)
            validated_data["firearm_details"] = serializer.save()
        return super().create(validated_data)


class DocumentOnOrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentOnOrganisation
        fields = [
            "document",
            "expiry_date",
            "document_type",
            "organisation",
            "reference_code",
        ]
        extra_kwargs = {
            "document": {"required": False},
            "organisation": {"required": False},
        }


class GoodOnApplicationDocumentCreateSerializer(serializers.ModelSerializer):
    application = serializers.PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    good = serializers.PrimaryKeyRelatedField(queryset=Good.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=ExporterUser.objects.all())
    document_on_organisation = DocumentOnOrganisationSerializer(required=False, write_only=True)

    class Meta:
        model = GoodOnApplicationDocument
        fields = (
            "name",
            "s3_key",
            "user",
            "size",
            "application",
            "good",
            "document_on_organisation",
            "document_type",
            "good_on_application",
        )

    def create(self, validated_data):
        document_on_organisation = validated_data.pop("document_on_organisation", None)
        document = super().create(validated_data)
        document.save()
        if document_on_organisation:
            serializer = DocumentOnOrganisationSerializer(
                data={
                    "document": document.pk,
                    "organisation": document.application.organisation.pk,
                    **document_on_organisation,
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            audit_trail_service.create(
                actor=validated_data["user"],
                verb=AuditType.DOCUMENT_ON_ORGANISATION_CREATE,
                target=document.application.organisation,
                payload={
                    "file_name": validated_data.get("name"),
                    "document_type": document_on_organisation.get("document_type"),
                },
            )

        process_document(document)
        return document


class GoodOnApplicationDocumentViewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    name = serializers.CharField()
    user = ExporterUserSimpleSerializer()
    s3_key = serializers.SerializerMethodField()
    safe = serializers.BooleanField()
    document_type = serializers.CharField()
    good_on_application = serializers.PrimaryKeyRelatedField(read_only=True)

    def get_s3_key(self, instance):
        return instance.s3_key if instance.safe else "File not ready"


class GoodOnApplicationInternalDocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodOnApplicationInternalDocument

        fields = (
            "name",
            "s3_key",
            "size",
            "safe",
            "document_title",
            "good_on_application",
        )

    def create(self, validated_data):
        document = super().create(validated_data)
        document.save()

        process_document(document)
        return document


class GoodOnApplicationInternalDocumentViewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    name = serializers.CharField()
    s3_key = serializers.SerializerMethodField()
    safe = serializers.BooleanField()
    document_title = serializers.CharField()

    def get_s3_key(self, instance):
        return instance.s3_key if instance.safe else "File not ready"
