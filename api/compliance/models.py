import uuid

from django.db import models
from django.utils import timezone

from api.cases.enums import CaseTypeEnum
from api.cases.models import Case
from api.common.models import TimestampableModel
from api.compliance.enums import ComplianceVisitTypes, ComplianceRiskValues
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class ComplianceSiteCase(Case):
    site = models.OneToOneField(
        "organisations.Site",
        related_name="compliance",
        on_delete=models.DO_NOTHING,
    )

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
    licence_risk_value = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        default=None,
    )  # value between 1 and 5

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


class CompliancePerson(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(null=False, blank=False, max_length=100)
    job_title = models.CharField(null=False, blank=False, max_length=100)
    visit_case = models.ForeignKey(
        ComplianceVisitCase, related_name="people_present", null=False, blank=False, on_delete=models.CASCADE
    )
