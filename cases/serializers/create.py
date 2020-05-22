from rest_framework import serializers

from cases.enums import ECJUQueryType
from cases.models import Case, CaseDocument, EcjuQuery
from conf.serializers import KeyValueChoiceField
from documents.libraries.process_document import process_document
from users.enums import UserStatuses
from users.models import GovUser


class CaseDocumentCreateSerializer(serializers.ModelSerializer):
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=GovUser.objects.all())

    class Meta:
        model = CaseDocument
        fields = (
            "name",
            "s3_key",
            "user",
            "size",
            "case",
            "description",
            "visible_to_exporter",
        )

    def create(self, validated_data):
        case_document = super(CaseDocumentCreateSerializer, self).create(validated_data)
        case_document.save()
        process_document(case_document)
        return case_document


class EcjuQueryCreateSerializer(serializers.ModelSerializer):
    """
    Create specific serializer, which does not take a response as gov users don't respond to their own queries!
    """

    question = serializers.CharField(max_length=5000, allow_blank=False, allow_null=False)
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    query_type = KeyValueChoiceField(choices=ECJUQueryType.choices)

    class Meta:
        model = EcjuQuery
        fields = (
            "id",
            "question",
            "case",
            "raised_by_user",
            "query_type",
        )


class CaseOfficerUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for assigning and removing case officers from a case.
    """

    case_officer = serializers.PrimaryKeyRelatedField(
        queryset=GovUser.objects.exclude(status=UserStatuses.DEACTIVATED).all(), allow_null=True
    )

    class Meta:
        model = Case
        fields = ("case_officer",)
