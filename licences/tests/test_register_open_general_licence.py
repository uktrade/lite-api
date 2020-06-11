from django.urls import reverse
from rest_framework import status

from cases.enums import CaseTypeEnum
from cases.models import CaseType
from open_general_licences.enums import OpenGeneralLicenceStatus
from open_general_licences.tests.factories import OpenGeneralLicenceFactory
from test_helpers.clients import DataTestClient


class RegisterOpenGeneralLicenceTests(DataTestClient):

    url = reverse("licences:open_general_licences")

    def setUp(self):
        super().setUp()
        self.open_general_licence = OpenGeneralLicenceFactory(case_type=CaseType.objects.get(id=CaseTypeEnum.OGTCL.id))

    def test_register_open_general_licence_success(self):
        data = {
            "open_general_licence": str(self.open_general_licence.id),
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqualIgnoreType(response_data["open_general_licence"], self.open_general_licence.id)

    def test_register_deactivated_open_general_licence_failure(self):
        self.open_general_licence.status = OpenGeneralLicenceStatus.DEACTIVATED
        self.open_general_licence.save()

        data = {
            "open_general_licence": str(self.open_general_licence.id),
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_registration_not_required_open_general_licence_failure(self):
        self.open_general_licence.registration_required = False
        self.open_general_licence.save()

        data = {
            "open_general_licence": str(self.open_general_licence.id),
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
