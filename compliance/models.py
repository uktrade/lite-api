from django.utils import timezone

from cases.enums import CaseTypeEnum
from cases.models import Case
import uuid

from django.db import models
from django.db.models import deletion, Q

from common.models import CreatedAt, TimestampableModel
from compliance.enums import ComplianceVisitTypes, ComplianceRiskValues
from licences.enums import LicenceStatus
from licences.models import Licence, GoodOnLicence
from organisations.models import Organisation
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class ComplianceSiteCase(Case):
    site = models.OneToOneField("organisations.Site", related_name="compliance", on_delete=models.DO_NOTHING,)

    def create_visit_case(self):
        """
        function to create a ComplianceVisitCase from a ComplianceSiteCase.
        :return: ComplianceVisitCase created
        """
        visit_case = ComplianceVisitCase(
            site_case=self,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
            organisation_id=self.organisation_id,
            case_type_id=CaseTypeEnum.COMPLIANCE_VISIT.id,
            submitted_at=timezone.now(),  # submitted_at is set since SLA falls over if not given
            case_officer=self.case_officer,
        )
        visit_case.save()
        return visit_case

    def get_licences(self):
        """
        Returns a list of licences belonging to the compliance case site
        """
        from compliance.helpers import COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES
        queryset = Case.objects.select_related("case_type").filter(
            Q(
                baseapplication__licence__status__in=[LicenceStatus.ISSUED, LicenceStatus.REINSTATED],
                baseapplication__application_sites__site__site_records_located_at__compliance__id=self.id,
            )
            | Q(opengenerallicencecase__site__site_records_located_at__compliance__id=self.id)
        )

        # We filter for OIEL, OICL and specific SIELs (dependant on CLC codes present) as these are the only case
        # types relevant for compliance cases
        approved_goods_on_licence = GoodOnLicence.objects.filter(
            good__good__control_list_entries__rating__regex=COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES
        ).values_list("good", flat=True)

        queryset = queryset.filter(
            case_type__id__in=[CaseTypeEnum.OICL.id, CaseTypeEnum.OIEL.id, *CaseTypeEnum.OGL_ID_LIST]
        ) | queryset.filter(baseapplication__goods__id__in=approved_goods_on_licence,)

        return queryset


class ComplianceVisitCase(Case):
    site_case = models.ForeignKey(
        ComplianceSiteCase, related_name="visit_case", on_delete=models.DO_NOTHING, blank=False, null=False
    )

    # visit report details
    visit_type = models.CharField(
        choices=ComplianceVisitTypes.choices, max_length=15, blank=True, null=True, default=None
    )
    visit_date = models.DateField(null=True, default=None)
    overall_risk_value = models.CharField(
        choices=ComplianceRiskValues.choices, max_length=10, blank=True, null=True, default=None
    )
    licence_risk_value = models.PositiveSmallIntegerField(blank=True, null=True, default=None,)  # value between 1 and 5

    overview = models.TextField(default=None, null=True)
    inspection = models.TextField(default=None, null=True)

    # compliance with licences
    compliance_overview = models.TextField(default=None, null=True)
    compliance_risk_value = models.CharField(
        choices=ComplianceRiskValues.choices, max_length=10, null=True, default=None
    )

    # knowledge and understanding demonstrated by key export individuals at meeting
    individuals_overview = models.TextField(default=None, null=True)
    individuals_risk_value = models.CharField(
        choices=ComplianceRiskValues.choices, max_length=10, null=True, default=None
    )

    # knowledge of controlled items of business' products
    products_overview = models.TextField(default=None, null=True)
    products_risk_value = models.CharField(choices=ComplianceRiskValues.choices, max_length=10, null=True, default=None)

    def get_licences(self):
        """
        Returns a list of licences belonging to the compliance case site
        """
        from compliance.helpers import COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES
        queryset = Case.objects.select_related("case_type").filter(
            Q(
                baseapplication__licence__status__in=[LicenceStatus.ISSUED, LicenceStatus.REINSTATED],
                baseapplication__application_sites__site__site_records_located_at__compliance__id=self.id,
            )
            | Q(opengenerallicencecase__site__site_records_located_at__compliance__id=self.id)
        )

        # We filter for OIEL, OICL and specific SIELs (dependant on CLC codes present) as these are the only case
        # types relevant for compliance cases
        approved_goods_on_licence = GoodOnLicence.objects.filter(
            good__good__control_list_entries__rating__regex=COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES
        ).values_list("good", flat=True)

        queryset = queryset.filter(
            case_type__id__in=[CaseTypeEnum.OICL.id, CaseTypeEnum.OIEL.id, *CaseTypeEnum.OGL_ID_LIST]
        ) | queryset.filter(baseapplication__goods__id__in=approved_goods_on_licence,)

        return queryset


class OpenLicenceReturns(CreatedAt):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(Organisation, on_delete=deletion.CASCADE)
    returns_data = models.TextField()
    year = models.PositiveSmallIntegerField()
    licences = models.ManyToManyField(Licence, related_name="open_licence_returns")


class CompliancePerson(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(null=False, blank=False, max_length=100)
    job_title = models.CharField(null=False, blank=False, max_length=100)
    visit_case = models.ForeignKey(
        ComplianceVisitCase, related_name="people_present", null=False, blank=False, on_delete=models.CASCADE
    )
