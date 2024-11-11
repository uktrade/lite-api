from rest_framework import serializers

from api.applications.models import (
    GoodOnApplication,
    PartyOnApplication,
    StandardApplication,
)
from api.cases.enums import LicenceDecisionType
from api.cases.models import Case
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.countries.models import Country


class LicenceDecisionSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    application_id = serializers.UUIDField(source="id")
    decision = serializers.CharField()
    decision_made_at = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = (
            "id",
            "application_id",
            "decision",
            "decision_made_at",
        )

    def get_licence_decision(self, case):
        if case.decision not in LicenceDecisionType.decisions():
            raise ValueError(f"Unknown decision type `{case.decision}`")

        return case.licence_decisions.filter(
            decision=case.decision,
        ).earliest("created_at")

    def get_id(self, case):
        return self.get_licence_decision(case).pk

    def get_decision_made_at(self, case):
        return self.get_licence_decision(case).created_at


class ApplicationSerializer(serializers.ModelSerializer):
    licence_type = serializers.CharField(source="case_type.reference")

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "reference_code",
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


class GoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodOnApplication
        fields = (
            "id",
            "application_id",
            "value",
        )


class AssessmentSerializer(serializers.ModelSerializer):
    good_id = serializers.UUIDField()

    class Meta:
        model = ControlListEntry
        fields = (
            "good_id",
            "rating",
        )
