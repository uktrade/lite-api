import datetime
import typing

from rest_framework import serializers

from api.applications.models import (
    GoodOnApplication,
    PartyOnApplication,
    StandardApplication,
)
from api.cases.enums import LicenceDecisionType
from api.cases.models import Case
from api.staticdata.countries.models import Country
from api.staticdata.report_summaries.models import ReportSummary


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


class GoodSerializer(serializers.ModelSerializer):
    application_id = serializers.UUIDField()
    unit = serializers.CharField()

    class Meta:
        model = GoodOnApplication
        fields = (
            "id",
            "application_id",
            "quantity",
            "unit",
            "value",
        )


class GoodDescriptionSerializer(serializers.ModelSerializer):
    description = serializers.CharField(source="name")
    good_id = serializers.UUIDField()

    class Meta:
        model = ReportSummary
        fields = (
            "description",
            "good_id",
        )


class ApplicationSerializer(serializers.ModelSerializer):
    licence_type = serializers.CharField(source="case_type.reference")
    status = serializers.CharField(source="status.status")
    processing_time = serializers.IntegerField(source="sla_days")
    sub_type = serializers.SerializerMethodField()
    first_closed_at = serializers.SerializerMethodField()

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "licence_type",
            "reference_code",
            "sub_type",
            "status",
            "processing_time",
            "first_closed_at",
        )

    def get_sub_type(self, application) -> str:
        if application.has_incorporated_goods:
            return "incorporation"

        return application.export_type

    def get_first_closed_at(self, application) -> typing.Optional[datetime.datetime]:
        if application.first_licence_decision_created_at:
            return application.first_licence_decision_created_at

        if application.baseapplication_ptr.case_ptr.closed_status_updates:
            return application.baseapplication_ptr.case_ptr.closed_status_updates[0].created_at

        return None
