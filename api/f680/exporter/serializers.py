from rest_framework import serializers

from api.organisations.exporter.serializers import RelatedOrganisationSerializer
from api.users.exporter.serializers import RelatedExporterUserSerializer

from api.f680.models import F680Application


class SectionType:
    SINGLE = "single"
    MULTIPLE = "multiple"


class F680ApplicationSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="status__status", read_only=True)
    organisation = RelatedOrganisationSerializer(read_only=True)
    submitted_by = RelatedExporterUserSerializer(read_only=True)

    class Meta:
        model = F680Application
        fields = [
            "id",
            "application",
            "status",
            "reference_code",
            "organisation",
            "submitted_at",
            "submitted_by",
        ]
        read_only_fields = ["id", "status", "reference_code", "organisation", "submitted_at", "submitted_by"]

    def create(self, validated_data):
        validated_data["organisation"] = self.context["organisation"]
        validated_data["status"] = self.context["default_status"]
        validated_data["case_type_id"] = self.context["case_type_id"]
        return super().create(validated_data)


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
    security_classification = FieldSerializer()
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
    security_classification = FieldSerializer(required=False)


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
    foi_reason = serializers.CharField(max_length=200, required=False)


class SubmittedApplicationJSONSerializer(serializers.Serializer):
    sections = SectionSerializer()
