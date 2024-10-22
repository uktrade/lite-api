from django.db.models import F
from rest_framework import serializers

from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.models import Case


class CaseLicenceSerializer(serializers.ModelSerializer):
    decision = serializers.SerializerMethodField()
    issued_date = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = (
            "id",
            "reference_code",
            "decision",
            "issued_date",
        )

    def get_decision(self, case):
        return "issued"

    def get_issued_date(self, case):
        return (
            case.licences.all()
            .annotate(issued_at=F("generatedcasedocument__created_at"))
            .earliest("issued_at")
            .issued_at
        )
