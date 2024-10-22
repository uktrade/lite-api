from enum import Enum

from django.db.models import F
from rest_framework import serializers

from api.cases.models import Case


class LicenceDecisionType(str, Enum):
    ISSUED = "issued"


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
        return LicenceDecisionType.ISSUED

    def get_decision_made_at(self, case):
        return case.licences.annotate(issued_at=F("generatedcasedocument__created_at")).earliest("issued_at").issued_at
