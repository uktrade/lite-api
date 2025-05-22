from rest_framework import serializers

from api.organisations.exporter.serializers import RelatedOrganisationSerializer
from api.users.exporter.serializers import RelatedExporterUserSerializer
from api.cases.serializers import CaseTypeSerializer
from api.f680.models import F680Application
from api.applications.serializers.fields import CaseStatusField
from api.users.serializers import UserNotificationsSerializer


class SectionType:
    SINGLE = "single"
    MULTIPLE = "multiple"


class F680ApplicationSerializer(UserNotificationsSerializer, serializers.ModelSerializer):
    status = CaseStatusField(read_only=True)
    organisation = RelatedOrganisationSerializer(read_only=True)
    submitted_by = RelatedExporterUserSerializer(read_only=True)
    case_type = serializers.SerializerMethodField()

    class Meta:
        model = F680Application
        fields = (
            "id",
            "name",
            "application",
            "status",
            "reference_code",
            "organisation",
            "submitted_at",
            "submitted_by",
            "case_type",
        ) + UserNotificationsSerializer.Meta.fields
        read_only_fields = ["id", "name", "status", "reference_code", "organisation", "submitted_at", "submitted_by"]

    def create(self, validated_data):
        validated_data["organisation"] = self.context["organisation"]
        validated_data["status"] = self.context["default_status"]
        validated_data["case_type_id"] = self.context["case_type_id"]
        return super().create(validated_data)

    def get_case_type(self, instance):
        return CaseTypeSerializer(instance.case_type).data

    def save(self, **kwargs):
        incoming_application_name = (
            self.validated_data.get("application", {})
            .get("sections", {})
            .get("general_application_details", {})
            .get("fields", {})
            .get("name", {})
            .get("answer", "")
        )

        if self.instance and not self.instance.name and incoming_application_name:
            self.instance.name = incoming_application_name
            self.instance.save()

        return super().save(**kwargs)


class FieldSerializer(serializers.Serializer):
    key = serializers.SlugField(max_length=50)
    answer = serializers.JSONField()
    raw_answer = serializers.JSONField()
    question = serializers.CharField(max_length=200)
    datatype = serializers.ChoiceField(choices=["list", "string", "boolean", "date"])


class UserItemFieldsSerializer(serializers.Serializer):
    entity_type = FieldSerializer()
    end_user_name = FieldSerializer()
    address = FieldSerializer()
    country = FieldSerializer()
    prefix = FieldSerializer()
    other_prefix = FieldSerializer(required=False)
    security_classification = FieldSerializer()
    other_security_classification = FieldSerializer(required=False)
    end_user_intended_end_use = FieldSerializer()
    third_party_role = FieldSerializer(required=False)
    third_party_role_other = FieldSerializer(required=False)


class UserItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    fields = UserItemFieldsSerializer()


class UserInformationSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=[SectionType.MULTIPLE])
    items = UserItemSerializer(many=True, min_length=1)


class ProductInformationFieldsSerializer(serializers.Serializer):
    product_name = FieldSerializer()
    product_description = FieldSerializer()
    prefix = FieldSerializer()
    other_prefix = FieldSerializer(required=False)
    security_classification = FieldSerializer(required=False)
    other_security_classification = FieldSerializer(required=False)


class ProductInformationSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=[SectionType.SINGLE])
    fields = ProductInformationFieldsSerializer()


class GeneralApplicationDetailsFieldsSerializer(serializers.Serializer):
    name = FieldSerializer()


class GeneralApplicationDetailsSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=[SectionType.SINGLE])
    fields = GeneralApplicationDetailsFieldsSerializer()


class ApprovalTypeFieldsSerializer(serializers.Serializer):
    approval_choices = FieldSerializer()


class ApprovalTypeSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=[SectionType.SINGLE])
    fields = ApprovalTypeFieldsSerializer()


class SectionSerializer(serializers.Serializer):
    product_information = ProductInformationSerializer()
    user_information = UserInformationSerializer()
    general_application_details = GeneralApplicationDetailsSerializer()
    approval_type = ApprovalTypeSerializer()


class FoiDeclarationSerializer(serializers.Serializer):
    agreed_to_foi = serializers.BooleanField()
    foi_reason = serializers.CharField(max_length=200, required=False, allow_blank=True)


class SubmittedApplicationJSONSerializer(serializers.Serializer):
    sections = SectionSerializer()
