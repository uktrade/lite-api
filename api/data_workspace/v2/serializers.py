from enum import Enum

from django.db.models import F
from rest_framework import serializers

from api.cases.models import Case
from api.cases.generated_documents.models import GeneratedCaseDocument

SIEL_TEMPLATE_ID = "d159b195-9256-4a00-9bc8-1eb2cebfa1d2"
SIEL_REFUSAL_TEMPLATE_ID = "074d8a54-ee10-4dca-82ba-650460650342"


class LicenceDecisionType(str, Enum):
    ISSUED = "issued"
    REFUSED = "refused"


class LicenceDecisionSerializer(serializers.ModelSerializer):
    decision = serializers.SerializerMethodField()
    decision_made_at = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = (
            "id",
            "reference_code",
            "decision",
            "decision_made_at",
        )

    def get_decision(self, case):
        if case.licences.count():
            return LicenceDecisionType.ISSUED
        else:
            return LicenceDecisionType.REFUSED

    def get_decision_made_at(self, case):
        if not case.licences.count():
            return GeneratedCaseDocument.objects.get(case=case, template_id=SIEL_REFUSAL_TEMPLATE_ID).created_at

        return case.licences.annotate(issued_at=F("generatedcasedocument__created_at")).earliest("issued_at").issued_at
