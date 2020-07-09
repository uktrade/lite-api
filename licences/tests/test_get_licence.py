from django.urls import reverse
from rest_framework import status

from cases.enums import CaseTypeEnum
from test_helpers.clients import DataTestClient


class GetLicenceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.f680_application = self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.F680)
        self.gifting_application = self.create_mod_clearance_application_case(self.organisation, CaseTypeEnum.GIFTING)
        self.exhibition_application = self.create_mod_clearance_application_case(
            self.organisation, CaseTypeEnum.EXHIBITION
        )
        self.open_application = self.create_open_application_case(self.organisation)
        self.applications = [
            self.standard_application,
            self.f680_application,
            self.gifting_application,
            self.exhibition_application,
            self.open_application,
        ]
        self.licences = {
            application: self.create_licence(application, is_complete=True) for application in self.applications
        }

    def test_get_licence(self):
        for licence in self.licences.values():
            url = reverse("licences:licence", kwargs={"pk": str(licence.id)})
            response = self.client.get(url, **self.exporter_headers)

            self.assertEqual(response.status_code, status.HTTP_200_OK)
