from rest_framework import serializers

from api.organisations.exporter.serializers import RelatedOrganisationSerializer
from api.users.exporter.serializers import RelatedExporterUserSerializer

from api.f680.models import F680Application  # /PS-IGNORE


class F680ApplicationSerializer(serializers.ModelSerializer):  # /PS-IGNORE
    status = serializers.CharField(source="status__status", read_only=True)
    organisation = RelatedOrganisationSerializer(read_only=True)
    submitted_by = RelatedExporterUserSerializer(read_only=True)

    class Meta:
        model = F680Application  # /PS-IGNORE
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


def required_fields(required_keys, data):
    missing_keys = set(required_keys)
    for field in data["fields"]:
        missing_keys.discard(field["key"])
    if missing_keys:
        raise serializers.ValidationError(f"Required fields missing from section; {list(missing_keys)}")


class FieldSerializer(serializers.Serializer):
    key = serializers.SlugField(max_length=50)
    answer = serializers.JSONField()
    raw_answer = serializers.JSONField()
    question = serializers.CharField(max_length=200)
    datatype = serializers.ChoiceField(choices=["list", "string", "boolean", "date"])


class UserItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    fields = FieldSerializer(many=True)

    def validate(self, data):
        required_fields(
            [
                "entity_type",
                "end_user_name",
                "address",
                "country",
                "security_classification",
                "end_user_intended_end_use",
            ],
            data,
        )
        return data


class UserInformationSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["multiple"])
    items = UserItemSerializer(many=True)


class ProductInformationSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["single"])
    fields = FieldSerializer(many=True)

    def validate(self, data):
        required_fields(["product_name", "product_description"], data)
        return data


class GeneralApplicationDetailsSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["single"])
    fields = FieldSerializer(many=True)

    def validate(self, data):
        required_fields(["name"], data)
        return data


class ApprovalTypeSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["single"])
    fields = FieldSerializer(many=True)

    def validate(self, data):
        required_fields(["approval_choices"], data)
        return data


class SectionSerializer(serializers.Serializer):
    product_information = ProductInformationSerializer()
    user_information = UserInformationSerializer()
    general_application_details = GeneralApplicationDetailsSerializer()
    approval_type = ApprovalTypeSerializer()


class SubmittedApplicationJSONSerializer(serializers.Serializer):
    sections = SectionSerializer()
