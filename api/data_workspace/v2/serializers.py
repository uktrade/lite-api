import typing
import uuid

from rest_framework import serializers

from api.applications.models import PartyOnApplication
from api.cases.enums import LicenceDecisionType
from api.cases.models import LicenceDecision
from api.staticdata.countries.models import Country


class LicenceDecisionSerializer(serializers.ModelSerializer):
    application_id = serializers.UUIDField(source="case.id")
    decision_made_at = serializers.DateTimeField(source="created_at")
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

    def get_licence_id(self, licence_decision) -> typing.Optional[uuid.UUID]:
        if licence_decision.decision in [LicenceDecisionType.REFUSED]:
            return None

        latest_decision = licence_decision.case.licence_decisions.exclude(
            excluded_from_statistics_reason__isnull=False
        ).last()

        if not latest_decision.licence:
            return None

        return latest_decision.licence.pk


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
