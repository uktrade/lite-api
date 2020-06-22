from django.urls import reverse

from compliance.tests.factories import ComplianceSiteCaseFactory
from test_helpers.clients import DataTestClient


class GetComplianceLicencesTests(DataTestClient):
    def test_get_compliance_licences(self):
        compliance_case = ComplianceSiteCaseFactory(organisation=self.organisation, site=self.organisation.primary_site)
        application = self.create_open_application_case(self.organisation)
        licence = self.create_licence(application, is_complete=True)

        url = reverse("compliance:licences", kwargs={"pk": compliance_case.id})
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()["results"]

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["id"], str(licence.application_id))
        self.assertEqual(response_data[0]["reference_code"], licence.application.reference_code)
        self.assertEqual(response_data[0]["status"]["key"], licence.application.status.status)
