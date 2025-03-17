from rest_framework import serializers

from api.applications.serializers.fields import CaseStatusField
from api.core.serializers import CountrySerializerField, KeyValueChoiceField
from api.organisations.exporter.serializers import RelatedOrganisationSerializer
from api.users.exporter.serializers import RelatedExporterUserSerializer

from api.f680.models import F680Application, Product, Recipient, SecurityReleaseRequest
from api.f680 import enums


class ProductSerializer(serializers.ModelSerializer):
    security_grading = KeyValueChoiceField(choices=enums.SecurityGrading.product_choices)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "security_grading",
            "security_grading_other",
        ]


class RecipientSerializer(serializers.ModelSerializer):
    country = CountrySerializerField()
    type = KeyValueChoiceField(choices=enums.RecipientType.choices)

    class Meta:
        model = Recipient
        fields = [
            "id",
            "name",
            "address",
            "country",
            "type",
            "role",
            "role_other",
        ]


class SecurityReleaseRequestSerializer(serializers.ModelSerializer):
    recipient = RecipientSerializer()
    product_id = serializers.UUIDField()
    security_grading = KeyValueChoiceField(choices=enums.SecurityGrading.security_release_choices)

    class Meta:
        model = SecurityReleaseRequest
        fields = [
            "id",
            "recipient",
            "security_grading",
            "security_grading_other",
            "approval_types",
            "intended_use",
            "product_id",
        ]


class F680ApplicationSerializer(serializers.ModelSerializer):
    status = CaseStatusField(read_only=True)
    organisation = RelatedOrganisationSerializer(read_only=True)
    submitted_by = RelatedExporterUserSerializer(read_only=True)
    security_release_requests = SecurityReleaseRequestSerializer(many=True)
    product = ProductSerializer(source="get_product")

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
            "name",
            "security_release_requests",
            "product",
        ]
        read_only_fields = ["id", "status", "reference_code", "organisation", "submitted_at", "submitted_by"]
