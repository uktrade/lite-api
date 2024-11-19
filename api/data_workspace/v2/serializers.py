from rest_framework import serializers


from api.applications.models import (
    GoodOnApplication,
    PartyOnApplication,
    StandardApplication,
)
from api.cases.enums import LicenceDecisionType
from api.cases.models import LicenceDecision
from api.licences.models import GoodOnLicence
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.countries.models import Country
from api.staticdata.report_summaries.models import ReportSummary
from api.staticdata.statuses.enums import CaseStatusEnum


class LicenceDecisionSerializer(serializers.ModelSerializer):
    application_id = serializers.CharField(source="case.id")
    decision = serializers.SerializerMethodField()
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

    def get_decision(self, licence_decision):
        if licence_decision.decision != LicenceDecisionType.ISSUED:
            return licence_decision.decision

        all_issued = all(
            ld.decision == LicenceDecisionType.ISSUED
            for ld in licence_decision.case.licence_decisions.all()
            if not ld.excluded_from_statistics_reason
        )
        if all_issued:
            return licence_decision.decision

        licence_decisions = sorted(
            [ld for ld in licence_decision.case.licence_decisions.all()], key=lambda ld: ld.created_at
        )
        presumed_licence_decision = licence_decisions[-1]

        if presumed_licence_decision.decision == LicenceDecisionType.ISSUED:
            return "issued_on_appeal"

        return licence_decision.decision

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


class ApplicationSerializer(serializers.ModelSerializer):
    licence_type = serializers.CharField(source="case_type.reference")
    sub_type = serializers.SerializerMethodField()
    status = serializers.CharField(source="status.status")

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "licence_type",
            "reference_code",
            "sub_type",
            "status",
            "sla_days",
        )

    def get_sub_type(self, application):
        if any(g.is_good_incorporated or g.is_onward_incorporated for g in application.goods.all()):
            return "incorporation"

        if application.export_type:
            return application.export_type

        raise Exception("Unknown sub-type")


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
            "quantity",
            "unit",
            "value",
        )


class GoodRatingSerializer(serializers.ModelSerializer):
    good_id = serializers.UUIDField()

    class Meta:
        model = ControlListEntry
        fields = (
            "good_id",
            "rating",
        )


class GoodOnLicenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodOnLicence
        fields = (
            "id",
            "good_id",
            "licence_id",
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


class LicenceRefusalCriteriaSerializer(serializers.Serializer):
    criteria = serializers.CharField(source="denial_reasons__display_value")
    licence_decision_id = serializers.UUIDField(source="case__licence_decisions__id")


class FootnoteSerializer(serializers.Serializer):
    footnote = serializers.CharField()
    team_name = serializers.CharField(source="team__name")
    application_id = serializers.CharField(source="case__pk")
    type = serializers.CharField()


class UnitSerializer(serializers.Serializer):
    code = serializers.CharField()
    description = serializers.CharField()


class StatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    name = serializers.CharField()
    is_closed = serializers.SerializerMethodField()

    def get_is_closed(self, status):
        return CaseStatusEnum.is_closed(status["status"])
