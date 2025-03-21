from rest_framework import serializers

from api.applications.models import StandardApplication


class ExportLicenceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": "Enter a reference name for the application"},
    )

    class Meta:
        model = StandardApplication
        fields = [
            "id",
            "name",
            "export_type",
            "have_you_been_informed",
            "reference_number_on_information_form",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "have_you_been_informed": {"required": True},
        }

    def create(self, validated_data):
        validated_data["organisation"] = self.context["organisation"]
        validated_data["status"] = self.context["default_status"]
        validated_data["case_type_id"] = self.context["case_type_id"]
        return super().create(validated_data)
