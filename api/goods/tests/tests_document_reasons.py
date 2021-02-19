from parameterized import parameterized
from unittest import mock

from django.urls import reverse
from rest_framework import status

from lite_content.lite_api import strings
from api.staticdata.missing_document_reasons.enums import GoodMissingDocumentReasons
from test_helpers.clients import DataTestClient


class GoodDocumentAvaiabilityandSensitivityTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.good = self.create_good("a good", self.organisation)
        self.document_availability_url = reverse("goods:good_document_availability", kwargs={"pk": self.good.id})
        self.document_sensitivity_url = reverse("goods:good_document_sensitivity", kwargs={"pk": self.good.id})

    @parameterized.expand(
        [[{"is_document_available": "yes"}], [{"is_document_available": "no"}],]
    )
    def test_document_available_to_upload(self, data):
        response = self.client.post(self.document_availability_url, data, **self.exporter_headers)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertTrue("good" in response.json())

    def test_document_available_to_upload_failure(self):
        data = {"is_document_available": None}
        response = self.client.post(self.document_availability_url, data, **self.exporter_headers)

        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
        errors = response.json()["errors"]
        self.assertTrue("is_document_available" in errors)
        self.assertEquals(errors["is_document_available"][0], "Select yes or no")

    @parameterized.expand(
        [[{"is_document_sensitive": "yes"}], [{"is_document_sensitive": "no"}],]
    )
    def test_document_sensitive(self, data):
        response = self.client.post(self.document_sensitivity_url, data, **self.exporter_headers)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertTrue("good" in response.json())

    def test_document_sensitivity_empty_failure(self):
        data = {"is_document_sensitive": None}
        response = self.client.post(self.document_sensitivity_url, data, **self.exporter_headers)

        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
        errors = response.json()["errors"]
        self.assertTrue("is_document_sensitive" in errors)
        self.assertEquals(errors["is_document_sensitive"][0], "Select yes or no")
