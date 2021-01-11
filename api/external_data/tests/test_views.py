import os

from test_helpers.clients import DataTestClient

from django.conf import settings

from django.urls import reverse

from api.external_data import models


class DenialViewSetTests(DataTestClient):
    def test_create_success(self):
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_valid.csv")
        response = self.client.post(url, {"csv_file": open(file_path, "rb")}, format="multipart", **self.gov_headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(models.Denial.objects.count(), 3)
        self.assertEqual(
            list(models.Denial.objects.values("authority", "denied_name", "data")),
            [
                {
                    "authority": "Foo Example",
                    "denied_name": "org1",
                    "data": {
                        "authority": "commercial",
                        "denial_type": "123 fake street",
                        "denied_name": "end_user",
                        "organisation_type": "https://www.example.com",
                    },
                },
                {
                    "authority": "Bar Example",
                    "denied_name": "org1",
                    "data": {
                        "authority": "commercial",
                        "denial_type": "456 fake street",
                        "denied_name": "end_user",
                        "organisation_type": "",
                    },
                },
                {
                    "authority": "Baz Example",
                    "denied_name": "org1",
                    "data": {
                        "authority": "commercial",
                        "denial_type": "789 fake street",
                        "denied_name": "end_user",
                        "organisation_type": "",
                    },
                },
            ],
        )

    def test_create_validation_error(self):
        url = reverse("external_data:denial-list")
        file_path = os.path.join(settings.BASE_DIR, "external_data/tests/denial_invalid.csv")
        response = self.client.post(url, {"csv_file": open(file_path, "rb")}, format="multipart", **self.gov_headers)

        self.assertEqual(response.status_code, 400)
