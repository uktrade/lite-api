from rest_framework import serializers

from api.cases.enums import AdviceType
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.conf.serializers import KeyValueChoiceField
from gov_users.serializers import GovUserViewSerializer


class GeneratedCaseDocumentExporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "id",
            "name",
            "created_at",
        )


class GeneratedCaseDocumentGovSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "template",
            "text",
        )


class AdviceDocumentGovSerializer(serializers.ModelSerializer):
    user = GovUserViewSerializer()
    advice_type = KeyValueChoiceField(choices=AdviceType.choices)

    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "id",
            "advice_type",
            "user",
            "created_at",
        )
