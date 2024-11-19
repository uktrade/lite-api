from rest_framework import serializers

from api.applications.models import PartyOnApplication
from api.cases.enums import LicenceDecisionType
from api.cases.models import LicenceDecision
from api.staticdata.countries.models import Country


class LicenceDecisionSerializer(serializers.ModelSerializer):
    application_id = serializers.CharField(source="case.id")
    decision_made_at = serializers.CharField(source="created_at")
    licence_id = serializers.SerializerMethodField()

    class Meta:
        model = LicenceDecision
        fields = (
            "id",
            "application_id",
            "decision",
            "decision_made_at",
            "licence_id",
        )

    def get_licence_id(self, licence_decision):
        if licence_decision.decision in [LicenceDecisionType.REFUSED]:
            return None

        licence_decisions = licence_decision.case.licence_decisions.all()
        licence_decisions = [
            ld for ld in licence_decision.case.licence_decisions.all() if ld.decision == LicenceDecisionType.ISSUED
        ]
        licence_decisions = sorted(licence_decisions, key=lambda ld: ld.created_at)
        licence_decision = licence_decisions[-1]

        if not licence_decision.licence:
            return None

        return licence_decision.licence.pk


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
