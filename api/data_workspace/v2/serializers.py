import datetime
import itertools
import typing

from rest_framework import serializers

from api.applications.models import (
    GoodOnApplication,
    PartyOnApplication,
    StandardApplication,
)
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import LicenceDecisionType
from api.cases.models import Case
from api.staticdata.countries.models import Country
from api.staticdata.statuses.enums import CaseStatusEnum


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
        if any(g.is_good_incorporated or g.is_onward_incorporated for g in application.goods.all()):
            return "incorporation"

        if application.export_type:
            return application.export_type

        raise Exception("Unknown sub-type")

    def get_first_closed_at(self, application) -> typing.Optional[datetime.datetime]:
        if application.licence_decisions.exists():
            return application.licence_decisions.earliest("created_at").created_at

        status_map = dict(CaseStatusEnum.choices)
        closed_statuses = list(
            itertools.chain.from_iterable((status, status_map[status]) for status in CaseStatusEnum.closed_statuses())
        )
        try:
            first_closed_status_update = Audit.objects.filter(
                target_object_id=application.pk,
                verb=AuditType.UPDATED_STATUS,
                payload__status__new__in=closed_statuses,
            ).earliest("created_at")
        except Audit.DoesNotExist:
            return None

        return first_closed_status_update.created_at
