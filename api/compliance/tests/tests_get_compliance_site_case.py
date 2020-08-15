from django.urls import reverse
from django.utils import timezone

from cases.enums import CaseTypeReferenceEnum
from api.compliance.tests.factories import ComplianceSiteCaseFactory, OpenLicenceReturnsFactory
from api.licences.enums import LicenceStatus
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from test_helpers.clients import DataTestClient


def _assert_response_data(self, response_data, compliance_case, open_licence_returns):
    self.assertEqual(response_data["id"], str(compliance_case.id))
    self.assertEqual(response_data["reference_code"], compliance_case.reference_code)
    self.assertEqual(response_data["case_type"]["reference"]["key"], CaseTypeReferenceEnum.COMP_SITE)
    self.assertEqual(response_data["data"]["address"]["id"], str(self.organisation.primary_site.address.id))
    self.assertEqual(
        response_data["data"]["address"]["address_line_1"], self.organisation.primary_site.address.address_line_1
    )
    self.assertEqual(
        response_data["data"]["address"]["address_line_2"], self.organisation.primary_site.address.address_line_2
    )
    self.assertEqual(response_data["data"]["address"]["city"], self.organisation.primary_site.address.city)
    self.assertEqual(response_data["data"]["address"]["region"], self.organisation.primary_site.address.region)
    self.assertEqual(response_data["data"]["address"]["postcode"], self.organisation.primary_site.address.postcode)
    self.assertEqual(
        response_data["data"]["address"]["country"]["id"], self.organisation.primary_site.address.country.id
    )
    self.assertEqual(response_data["data"]["site_name"], self.organisation.primary_site.name)
    self.assertEqual(response_data["data"]["status"]["key"], compliance_case.status.status)
    self.assertEqual(response_data["data"]["organisation"]["id"], str(self.organisation.id))
    self.assertEqual(len(response_data["data"]["open_licence_returns"]), 1)
    self.assertEqual(response_data["data"]["open_licence_returns"][0]["id"], str(open_licence_returns.id))
    self.assertEqual(response_data["data"]["open_licence_returns"][0]["year"], open_licence_returns.year)
    self.assertIsNotNone(response_data["data"]["open_licence_returns"][0]["created_at"])


class GetComplianceSiteCaseTests(DataTestClient):
    def test_get_compliance_case(self):
        application = self.create_open_application_case(self.organisation)
        compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )
        open_licence_returns = OpenLicenceReturnsFactory(organisation=self.organisation)
        licence = self.create_licence(application, status=LicenceStatus.ISSUED)
        open_licence_returns.licences.set([licence])

        url = reverse("cases:case", kwargs={"pk": compliance_case.id})
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["case"]

        _assert_response_data(self, response_data, compliance_case, open_licence_returns)

    def test_get_compliance_visit_cases_as_part_of_site(self):
        compliance_case = ComplianceSiteCaseFactory(
            organisation=self.organisation,
            site=self.organisation.primary_site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
        )
        visit_case1 = compliance_case.create_visit_case()

        compliance_case.case_officer = self.gov_user
        compliance_case.save()

        visit_case2 = compliance_case.create_visit_case()
        visit_case2.visit_date = timezone.now().date()
        visit_case2.save()

        url = reverse("cases:case", kwargs={"pk": compliance_case.id})
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["case"]

        self.assertEqual(len(response_data["data"]["visits"]), 2)
        for visit in response_data["data"]["visits"]:
            if visit["id"] == str(visit_case1.id):
                self.assertEqual(visit["reference_code"], visit_case1.reference_code)
                self.assertEqual(visit["case_officer"], None)
                self.assertEqual(visit["visit_date"], None)
            elif visit["id"] == str(visit_case2.id):
                self.assertEqual(visit["reference_code"], visit_case2.reference_code)
                self.assertEqual(
                    visit["case_officer"], f"{visit_case2.case_officer.first_name} {visit_case2.case_officer.last_name}"
                )
                self.assertEqual(
                    visit["case_officer"],
                    f"{compliance_case.case_officer.first_name} {compliance_case.case_officer.last_name}",
                )
                self.assertEqual(visit["visit_date"], visit_case2.visit_date.strftime("%Y-%m-%d"))
            else:
                self.assertTrue(False)
