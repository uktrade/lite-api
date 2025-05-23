import datetime
import typing
import uuid

from rest_framework import serializers

from api.applications.models import (
    GoodOnApplication,
    PartyOnApplication,
    StandardApplication,
)
from api.cases.enums import LicenceDecisionType
from api.cases.models import LicenceDecision
from api.licences.models import GoodOnLicence
from api.staticdata.countries.models import Country
from api.staticdata.denial_reasons.models import DenialReason


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
        # A refusal won't have a licence generated as only an approved
        # application ends up with a licence so we can return early.
        if licence_decision.decision == LicenceDecisionType.REFUSED:
            return None

        unexcluded_licence_decisions = licence_decision.case.unexcluded_licence_decisions
        if licence_decision.decision == LicenceDecisionType.ISSUED:
            # There is a potential edge case here where an issued licence has
            # been ultimately refused because the case was re-opened for changes
            # and those changes resulted in a refusal.
            # In this case we want to only get the latest licences of all the
            # issued decisions instead of potentially returning `None` for the
            # refusal decision.
            unexcluded_licence_decisions = [
                ld for ld in unexcluded_licence_decisions if ld.decision == LicenceDecisionType.ISSUED
            ]

        latest_decision = unexcluded_licence_decisions[0]
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


class GoodDescriptionSerializer(serializers.Serializer):
    description = serializers.SerializerMethodField()
    good_id = serializers.UUIDField(source="id")

    def get_description(self, instance) -> str:
        prefix = instance.report_summary_prefix_name
        subject = instance.report_summary_subject_name

        if prefix:
            return f"{prefix} {subject}"

        return subject


class GoodOnLicenceSerializer(serializers.ModelSerializer):
    good_id = serializers.UUIDField()
    licence_id = serializers.UUIDField()

    class Meta:
        model = GoodOnLicence
        fields = ("good_id", "licence_id")


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


class UnitSerializer(serializers.Serializer):
    code = serializers.CharField()
    description = serializers.CharField()


class FootnoteSerializer(serializers.Serializer):
    footnote = serializers.CharField()
    team_name = serializers.CharField(source="team__name")
    application_id = serializers.CharField(source="case__pk")
    type = serializers.CharField()


class GoodRatingSerializer(serializers.Serializer):
    good_id = serializers.UUIDField(source="id")
    rating = serializers.CharField()


class LicenceRefusalCriteriaSerializer(serializers.ModelSerializer):
    criteria = serializers.CharField(source="display_value")
    licence_decision_id = serializers.UUIDField()

    class Meta:
        model = DenialReason
        fields = ("criteria", "licence_decision_id")
