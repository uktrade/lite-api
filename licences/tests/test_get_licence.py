from django.urls import reverse
from rest_framework import status

from cases.enums import CaseTypeEnum
from licences.enums import LicenceStatus
from test_helpers.clients import DataTestClient


class GetLicenceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.applications = [
            self.create_standard_application_case(self.organisation),
            self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.F680),
            self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.GIFTING),
            self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.EXHIBITION),
            self.create_open_application_case(self.organisation),
        ]
        self.licences = {
            application: self.create_licence(application, status=LicenceStatus.ISSUED)
            for application in self.applications
        }

    def test_get_licence_exporter_view(self):
        for application, licence in self.licences.items():
            url = reverse("licences:licence", kwargs={"pk": str(licence.id)})
            response = self.client.get(url, **self.exporter_headers)
            response_data = response.json()

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response_data["application"]["id"], str(application.id))
            self.assertEqual(response_data["reference_code"], str(licence.reference_code))
            self.assertEqual(response_data["duration"], licence.duration)
            self.assertEqual(response_data["start_date"], licence.start_date.strftime("%Y-%m-%d"))
