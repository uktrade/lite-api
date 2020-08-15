from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized
from rest_framework import status

from cases.enums import CaseTypeEnum
from api.compliance.enums import ComplianceVisitTypes, ComplianceRiskValues
from api.compliance.models import ComplianceVisitCase
from api.compliance.tests.factories import ComplianceVisitCaseFactory, ComplianceSiteCaseFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class ComplianceVisitCaseTests(DataTestClient):
    def _validate_comp_visit(self, response, instance):
        self.assertEqual(response["visit_type"]["key"], instance.visit_type)
        self.assertEqual(response["visit_date"], instance.visit_date.strftime("%Y-%m-%d"))
        self.assertEqual(response["licence_risk_value"], instance.licence_risk_value)
        self.assertEqual(response["overall_risk_value"]["key"], instance.overall_risk_value)
        self.assertEqual(response["overview"], instance.overview)
        self.assertEqual(response["inspection"], instance.inspection)
        self.assertEqual(response["compliance_overview"], instance.compliance_overview)
        self.assertEqual(response["compliance_risk_value"]["key"], instance.compliance_risk_value)
        self.assertEqual(response["individuals_overview"], instance.individuals_overview)
        self.assertEqual(response["individuals_risk_value"]["key"], instance.individuals_risk_value)
        self.assertEqual(response["products_overview"], instance.products_overview)
        self.assertEqual(response["products_risk_value"]["key"], instance.products_risk_value)

    # Get a compliance visit case and check all of it's details
    def test_get_compliance_visit_case(self):
        comp_case = ComplianceVisitCaseFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )

        url = reverse("compliance:visit_case", kwargs={"pk": comp_case.id})
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self._validate_comp_visit(response_data, comp_case)

    # Update compliance visit Tests and check all the details are correctly returned
    @parameterized.expand(
        [
            ("visit_type", ComplianceVisitTypes.REVISIT, True),
            ("visit_date", (timezone.now() + timedelta(days=30)).date().strftime("%Y-%m-%d"), False),
            ("licence_risk_value", 3, False),
            ("overall_risk_value", ComplianceRiskValues.HIGHER, True),
            ("overview", "the overview", False),
            ("inspection", "inspection", False),
            ("compliance_overview", "compliance_overview", False),
            ("compliance_risk_value", ComplianceRiskValues.HIGHER, True),
            ("individuals_overview", "overview", False),
            ("individuals_risk_value", ComplianceRiskValues.HIGHER, True),
            ("products_overview", "another overview", False),
            ("products_risk_value", ComplianceRiskValues.HIGHER, True),
        ]
    )
    def test_update_compliance_visit_case(self, field, data, key):
        comp_case = ComplianceVisitCaseFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )
        json = {field: data}
        url = reverse("compliance:visit_case", kwargs={"pk": comp_case.id})
        response = self.client.patch(url, json, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if key:
            self.assertEqual(response_data[field]["key"], data)
        else:
            self.assertEqual(response_data[field], data)

    def test_create_compliance_visit_case(self):
        compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            case_officer_id=self.gov_user.id,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        data = {}

        url = reverse("compliance:compliance_visit", kwargs={"pk": compliance_case.id})
        response = self.client.post(url, data, **self.gov_headers)
        data = response.json()["data"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data["site_case_id"], str(compliance_case.id))
        self.assertEqual(data["site_case_reference_code"], compliance_case.reference_code)

        visit_case = ComplianceVisitCase.objects.get(id=data["id"])
        self.assertEqual(compliance_case.case_officer_id, visit_case.case_officer_id)
        self.assertEqual(visit_case.case_type.id, CaseTypeEnum.COMPLIANCE_VISIT.id)
