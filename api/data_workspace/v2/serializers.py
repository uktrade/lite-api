from rest_framework import serializers

from api.applications.models import PartyOnApplication, StandardApplication
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

    def get_decision(self, case):
        return case.decision

    def get_decision_made_at(self, case):
        if case.decision not in LicenceDecisionType.decisions():
            raise ValueError(f"Unknown decision type `{case.decision}`")

        return (
            case.licence_decisions.filter(
                decision=case.decision,
            )
            .earliest("created_at")
            .created_at
        )


class ApplicationSerializer(serializers.ModelSerializer):
    licence_type = serializers.CharField(source="case_type.reference")

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "licence_type",
        )


class CountrySerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="id")

    class Meta:
        model = Country
        fields = (
            "code",
            "name",
        )


class DestinationSerializer(serializers.ModelSerializer):
    country_code = serializers.CharField(source="party.country.id")
    application_id = serializers.CharField(source="application.id")
    type = serializers.CharField(source="party.type")

    class Meta:
        model = PartyOnApplication
        fields = (
            "country_code",
            "application_id",
            "type",
        )
