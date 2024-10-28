from enum import Enum

from rest_framework import serializers

from api.cases.models import Case

SIEL_TEMPLATE_ID = "d159b195-9256-4a00-9bc8-1eb2cebfa1d2"
SIEL_REFUSAL_TEMPLATE_ID = "074d8a54-ee10-4dca-82ba-650460650342"


class LicenceDecisionType(str, Enum):
    ISSUED = "issued"
    REFUSED = "refused"

    @classmethod
    def templates(cls):
        return {
            cls.ISSUED: SIEL_TEMPLATE_ID,
            cls.REFUSED: SIEL_REFUSAL_TEMPLATE_ID,
        }

    @classmethod
    def get_template(cls, decision):
        return cls.templates()[cls(decision)]


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
        return case.decision

    def get_decision_made_at(self, case):
        documents = case.casedocument_set.filter(
            generatedcasedocument__template_id=LicenceDecisionType.get_template(case.decision),
            safe=True,
            visible_to_exporter=True,
        )

        return documents.earliest("created_at").created_at
