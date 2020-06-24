from django.urls import reverse
from rest_framework import status

from compliance.tests.factories import ComplianceSiteCaseFactory
from conf.constants import GovPermissions
from lite_content.lite_api import strings
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


class ComplianceManageStatusTests(DataTestClient):
    def test_gov_set_compliance_status_to_closed_success(self):
        compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        url = reverse("compliance:manage_status", kwargs={"pk": compliance_case.id})
        data = {"status": CaseStatusEnum.CLOSED}
        response = self.client.put(url, data=data, **self.gov_headers)

        compliance_case.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(compliance_case.status.status, CaseStatusEnum.CLOSED)

    def test_gov_set_compliance_status_to_open_success(self):
        self.gov_user.role.permissions.set([GovPermissions.REOPEN_CLOSED_CASES.name])

        compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.CLOSED),
        )

        url = reverse("compliance:manage_status", kwargs={"pk": compliance_case.id})
        data = {"status": CaseStatusEnum.OPEN}
        response = self.client.put(url, data=data, **self.gov_headers)

        compliance_case.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(compliance_case.status.status, CaseStatusEnum.OPEN)

    def test_gov_set_compliance_status_to_withdrawn_failure(self):
        compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )

        url = reverse("compliance:manage_status", kwargs={"pk": compliance_case.id})
        data = {"status": CaseStatusEnum.WITHDRAWN}
        response = self.client.put(url, data=data, **self.gov_headers)

        compliance_case.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json().get("errors")["status"][0], strings.Statuses.BAD_STATUS)


# TODO: Add new compliance visit statuses tests
