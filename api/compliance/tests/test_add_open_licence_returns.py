from datetime import datetime

from rest_framework import status
from rest_framework.reverse import reverse

from api.compliance.models import OpenLicenceReturns
from api.licences.enums import LicenceStatus
from lite_content.lite_api.strings import Compliance
from test_helpers.clients import DataTestClient


class AddOpenLicenceReturnsTest(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("compliance:open_licence_returns")
        application = self.create_standard_application_case(self.organisation)
        self.licence = self.create_licence(application, status=LicenceStatus.ISSUED)

    @staticmethod
    def _create_open_licence_returns_csv(data):
        file = "\n"
        for reference_code in data:
            file += reference_code + ",1,2,3,4\n"
        return file

    def test_upload_licence_returns_success(self):
        data = {
            "file": self._create_open_licence_returns_csv([self.licence.reference_code]),
            "year": datetime.now().year,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            OpenLicenceReturns.objects.filter(
                organisation=self.organisation,
                returns_data=data["file"].strip(),
                year=data["year"],
                licences=self.licence,
            ).count(),
            1,
        )
        self.assertEqual(response.json()["open_licence_returns"], str(OpenLicenceReturns.objects.first().id))

    def test_upload_licence_returns_removes_invalid_characters_success(self):
        file_string = f'\n{self.licence.reference_code},"@123,",-44,=D9,+dj.\n'
        expected_cleaned_string = f"\n{self.licence.reference_code},123,,-44,D9,dj.\n".strip()
        data = {
            "file": file_string,
            "year": datetime.now().year,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(expected_cleaned_string, OpenLicenceReturns.objects.first().returns_data)
        self.assertEqual(response.json()["open_licence_returns"], str(OpenLicenceReturns.objects.first().id))

    def test_upload_licence_returns_no_year_failure(self):
        data = {
            "file": self._create_open_licence_returns_csv([self.licence.reference_code]),
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"year": [Compliance.OpenLicenceReturns.YEAR_ERROR]})
        self.assertFalse(OpenLicenceReturns.objects.exists())

    def test_upload_licence_returns_invalid_year_failure(self):
        data = {
            "file": self._create_open_licence_returns_csv([self.licence.reference_code]),
            "year": 2018,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"year": [Compliance.OpenLicenceReturns.INVALID_YEAR]})
        self.assertFalse(OpenLicenceReturns.objects.exists())

    def test_upload_licence_returns_no_file_failure(self):
        data = {
            "year": datetime.now().year,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"file": [Compliance.OpenLicenceReturns.FILE_ERROR]})
        self.assertFalse(OpenLicenceReturns.objects.exists())

    def test_upload_licence_returns_invalid_file_format_failure(self):
        data = {
            "file": "\na,b,c\n",
            "year": datetime.now().year,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"file": [Compliance.OpenLicenceReturns.INVALID_FILE_FORMAT]})
        self.assertFalse(OpenLicenceReturns.objects.exists())

    def test_upload_licence_returns_invalid_licences_failure(self):
        data = {
            "file": self._create_open_licence_returns_csv(["GB/blahblah"]),
            "year": datetime.now().year,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"file": [Compliance.OpenLicenceReturns.INVALID_LICENCES]})
        self.assertFalse(OpenLicenceReturns.objects.exists())

    def test_upload_licence_returns_non_org_licences_failure(self):
        organisation, _ = self.create_organisation_with_exporter_user()
        application = self.create_standard_application_case(organisation)
        licence = self.create_licence(application, status=LicenceStatus.ISSUED)

        data = {
            "file": self._create_open_licence_returns_csv([licence.reference_code]),
            "year": datetime.now().year,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"], {"file": [Compliance.OpenLicenceReturns.INVALID_LICENCES]})
        self.assertFalse(OpenLicenceReturns.objects.exists())
