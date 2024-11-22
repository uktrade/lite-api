import datetime

from rest_framework import serializers

from api.cases.enums import LicenceDecisionType
from api.cases.models import Case
from api.staticdata.countries.models import Country


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

    def get_decision(self, case) -> str:
        return case.decision

    def get_decision_made_at(self, case) -> datetime.datetime:
        if case.decision not in LicenceDecisionType.decisions():
            raise ValueError(f"Unknown decision type `{case.decision}`")  # pragma: no cover

        return (
            case.licence_decisions.filter(
                decision=case.decision,
            )
            .earliest("created_at")
            .created_at
        )


class CountrySerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="id")

    class Meta:
        model = Country
        fields = ("code", "name")
