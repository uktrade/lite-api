from django.utils import timezone
from rest_framework import serializers

from addresses.serializers import AddressSerializer
from cases.models import Case
from compliance.models import ComplianceSiteCase, ComplianceVisitCase, OpenLicenceReturns
from compliance.serializers.OpenLicenceReturns import OpenLicenceReturnsListSerializer
from conf.serializers import PrimaryKeyRelatedSerializerField
from licences.enums import LicenceStatus
from licences.models import Licence
from organisations.models import Organisation
from organisations.serializers import OrganisationDetailSerializer

from cases.libraries.get_flags import get_ordered_flags
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum
from teams.helpers import get_team_by_pk
from users.libraries.notifications import (
    get_exporter_user_notification_individual_count,
    get_exporter_user_notification_individual_count_with_compliance_visit,
)


class ComplianceSiteViewSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source="site.name")
    address = AddressSerializer(source="site.address")
    status = serializers.SerializerMethodField()
    organisation = PrimaryKeyRelatedSerializerField(
        queryset=Organisation.objects.all(), serializer=OrganisationDetailSerializer
    )
    open_licence_returns = serializers.SerializerMethodField()
    visits = serializers.SerializerMethodField()
    team = None

    class Meta:
        model = ComplianceSiteCase
        fields = (
            "address",
            "site_name",
            "status",
            "organisation",
            "visits",
            "open_licence_returns",
        )

    def __init__(self, *args, **kwargs):
        super(ComplianceSiteViewSerializer, self).__init__(*args, **kwargs)

        self.team = self.context.get("team")

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None

    def get_visits(self, instance):
        visit_cases = (
            ComplianceVisitCase.objects.select_related("case_officer", "case_type")
            .prefetch_related("flags")
            .filter(site_case_id=instance.id)
        )
        return [
            {
                "id": case.id,
                "reference_code": case.reference_code,
                "visit_date": case.visit_date,
                "case_officer": f"{case.case_officer.first_name} {case.case_officer.last_name}"
                if case.case_officer
                else None,
                "flags": get_ordered_flags(case=case, team=self.team, limit=3),
            }
            for case in visit_cases
        ]

    def get_open_licence_returns(self, instance):
        queryset = OpenLicenceReturns.objects.filter(organisation_id=instance.organisation_id).order_by(
            "-year", "-created_at"
        )

        return OpenLicenceReturnsListSerializer(queryset, many=True).data


class ComplianceLicenceListSerializer(serializers.ModelSerializer):
    flags = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    case_type = serializers.SerializerMethodField()
    team = None

    class Meta:
        model = Case
        fields = (
            "id",
            "case_type",
            "reference_code",
            "status",
            "flags",
        )

    def __init__(self, *args, **kwargs):
        super(ComplianceLicenceListSerializer, self).__init__(*args, **kwargs)

        self.team = get_team_by_pk(self.context.get("request").user.team_id)

    def get_flags(self, instance):
        return get_ordered_flags(case=instance, team=self.team, limit=3)

    def get_status(self, instance):
        # The latest non draft licence should be the only active licence on a case or the licence that was active
        last_licence = (
            Licence.objects.filter(application_id=instance.id)
            .exclude(status=LicenceStatus.DRAFT)
            .order_by("created_at")
            .last()
        )

        # not all case types contain a licence, for example OGLs do not. As a result we display the case status
        if last_licence:
            return {
                "key": last_licence.status,
                "value": LicenceStatus.human_readable(last_licence.status),
            }
        else:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }

    def get_case_type(self, instance):
        from cases.serializers import CaseTypeSerializer

        return CaseTypeSerializer(instance.case_type).data


class ExporterComplianceSiteListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_code = serializers.CharField()
    site_name = serializers.CharField(source="site.name")
    address = AddressSerializer(source="site.address")
    review_date = serializers.SerializerMethodField()

    def get_review_date(self, instance):
        comp_visit_case = (
            ComplianceVisitCase.objects.filter(site_case_id=instance.id, visit_date__gte=timezone.now().date())
            .order_by("visit_date")
            .first()
        )
        if comp_visit_case:
            return comp_visit_case.visit_date
        return None


class ExporterComplianceSiteDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_code = serializers.CharField()
    site_name = serializers.CharField(source="site.name")
    address = AddressSerializer(source="site.address")
    visit_date = serializers.SerializerMethodField()
    exporter_user_notification_count = serializers.SerializerMethodField()
    is_primary_site = serializers.SerializerMethodField()

    def get_visit_date(self, instance):
        # if review date exists get one in the future (nearest)
        # else determine most recent
        visit_cases = ComplianceVisitCase.objects.filter(site_case_id=instance.id).order_by("visit_date")
        if visit_cases.filter(visit_date__gte=timezone.now().date()).exists():
            return visit_cases.filter(visit_date__gte=timezone.now().date()).first().visit_date

        visit_case = visit_cases.last()

        if visit_case:
            return visit_case.visit_date

        return None

    def get_exporter_user_notification_count(self, instance):
        return get_exporter_user_notification_individual_count_with_compliance_visit(
            exporter_user=self.context.get("request").user,
            organisation_id=self.context.get("organisation").id,
            case=instance,
        )

    def get_is_primary_site(self, instance):
        return instance.site.id == self.context.get("organisation").primary_site_id


class ExporterComplianceVisitListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_code = serializers.CharField()
    visit_date = serializers.DateField()
    case_officer_first_name = serializers.CharField(source="case_officer.first_name", default=None)
    case_officer_last_name = serializers.CharField(source="case_officer.last_name", default=None)


class ExporterComplianceVisitDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_code = serializers.CharField()
    visit_date = serializers.DateField()
    case_officer_first_name = serializers.CharField(source="case_officer.first_name", default=None)
    case_officer_last_name = serializers.CharField(source="case_officer.last_name", default=None)
    exporter_user_notification_count = serializers.SerializerMethodField()

    def get_exporter_user_notification_count(self, instance):
        return get_exporter_user_notification_individual_count(
            exporter_user=self.context.get("request").user,
            organisation_id=self.context.get("organisation_id"),
            case=instance,
        )
