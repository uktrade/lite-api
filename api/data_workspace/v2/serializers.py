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
        if licence_decision.decision in [LicenceDecisionType.REFUSED, LicenceDecisionType.REVOKED]:
            return ""

        latest_decision = licence_decision.case.licence_decisions.order_by("created_at").last()

        return latest_decision.licence.id if latest_decision.licence else ""


class ApplicationSerializer(serializers.ModelSerializer):
    licence_type = serializers.CharField(source="case_type.reference")
    sub_type = serializers.SerializerMethodField()

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "licence_type",
            "reference_code",
            "sub_type",
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
