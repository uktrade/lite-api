from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.compliance.tests.factories import ComplianceSiteCaseFactory, ComplianceVisitCaseFactory, PeoplePresentFactory
from api.conf.constants import GovPermissions
from lite_content.lite_api import strings
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class ComplianceManageStatusTests(DataTestClient):
    def test_gov_set_compliance_case_status_to_closed_success(self):
        compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        url = reverse("cases:case", kwargs={"pk": compliance_case.id})
        data = {"status": CaseStatusEnum.CLOSED}
        response = self.client.patch(url, data=data, **self.gov_headers)

        compliance_case.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(compliance_case.status.status, CaseStatusEnum.CLOSED)

    def test_gov_set_compliance_case_status_to_open_success(self):
        self.gov_user.role.permissions.set([GovPermissions.REOPEN_CLOSED_CASES.name])

        compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.CLOSED),
        )

        url = reverse("cases:case", kwargs={"pk": compliance_case.id})
        data = {"status": CaseStatusEnum.OPEN}
        response = self.client.patch(url, data=data, **self.gov_headers)

        compliance_case.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(compliance_case.status.status, CaseStatusEnum.OPEN)

    def test_gov_set_compliance_case_status_to_withdrawn_failure(self):
        compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        url = reverse("cases:case", kwargs={"pk": compliance_case.id})
        data = {"status": CaseStatusEnum.WITHDRAWN}
        response = self.client.patch(url, data=data, **self.gov_headers)

        compliance_case.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get("errors")["status"][0], strings.Statuses.BAD_STATUS)

    @parameterized.expand(CaseStatusEnum.compliance_visit_statuses)
    def test_compliance_visit_case_all_applicable_statuses_setable(self, status_to_set):
        compliance_case = ComplianceVisitCaseFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )
        PeoplePresentFactory(visit_case=compliance_case)
        url = reverse("cases:case", kwargs={"pk": compliance_case.id})
        data = {"status": status_to_set}
        response = self.client.patch(url, data=data, **self.gov_headers)

        compliance_case.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(compliance_case.status.status, status_to_set)

    @parameterized.expand(
        [status[0] for status in CaseStatusEnum.choices if status[0] not in CaseStatusEnum.compliance_visit_statuses]
    )
    def test_compliance_visit_case_other_statuses_can_not_be_set(self, status_to_set):
        self.gov_user.role = self.super_user_role
        self.gov_user.save()
        compliance_case = ComplianceVisitCaseFactory(
            organisation=self.organisation, status=get_case_status_by_status(CaseStatusEnum.OPEN)
        )

        url = reverse("cases:case", kwargs={"pk": compliance_case.id})
        data = {"status": status_to_set}
        response = self.client.patch(url, data=data, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get("errors")["status"][0], strings.Statuses.BAD_STATUS)
