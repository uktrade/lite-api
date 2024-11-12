import datetime

from rest_framework import serializers

from api.applications.models import PartyOnApplication
from api.cases.enums import LicenceDecisionType
from api.cases.models import Case
from api.licences.models import Licence
from api.staticdata.countries.models import Country


class LicenceDecisionSerializer(serializers.ModelSerializer):
    decision = serializers.SerializerMethodField()
    decision_made_at = serializers.SerializerMethodField()
    licence_id = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = (
            "id",
            "reference_code",
            "decision",
            "decision_made_at",
            "licence_id",
        )

    def get_decision(self, case) -> str:
        return case.decision

    def get_decision_made_at(self, case) -> datetime.datetime:
        if case.decision not in LicenceDecisionType.decisions():
            raise ValueError(f"Unknown decision type `{case.decision}`")  # pragma: no cover

        return case.licence_decisions.filter(
            decision=case.decision,
        ).earliest("created_at")

    def get_id(self, case):
        return self.get_licence_decision(case).pk

    def get_decision_made_at(self, case):
        return self.get_licence_decision(case).created_at

    def get_licence_id(self, case):
        licence_decision = self.get_licence_decision(case)
        if licence_decision.decision != LicenceDecisionType.ISSUED:
            return None

        licences = licence_decision.case.licences.exclude(status="draft").order_by("created_at")
        try:
            return licences.get().pk
        except Licence.MultipleObjectsReturned:
            pass

        licences = licences.filter(status="cancelled")
        return licences.first().pk


class CountrySerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="id")

    class Meta:
        model = Country
        fields = (
            "code",
            "name",
        )


class DestinationSerializer(serializers.ModelSerializer):
    application_id = serializers.UUIDField()
    country_code = serializers.CharField(source="party.country.id")
    type = serializers.CharField(source="party.type")

    class Meta:
        model = PartyOnApplication
        fields = (
            "application_id",
            "country_code",
            "type",
        )
