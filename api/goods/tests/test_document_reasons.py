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

    @parameterized.expand([[{"is_document_available": "yes"}], [{"is_document_available": "no"}]])
    def test_document_available_to_upload(self, data):
        response = self.client.post(self.document_availability_url, data, **self.exporter_headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue("good" in response.json())

    def test_document_available_to_upload_failure(self):
        data = {"is_document_available": None}
        response = self.client.post(self.document_availability_url, data, **self.exporter_headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        errors = response.json()["errors"]
        self.assertTrue("is_document_available" in errors)
        self.assertEqual(errors["is_document_available"][0], "Select yes or no")

    def test_no_document_comments_required_when_no_document_attached(self):

        # Missing no_document_comments
        data = {"is_document_available": "no"}
        response = self.client.post(self.document_availability_url, data, **self.exporter_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = {"is_document_available": "no", "no_document_comments": ""}
        response = self.client.post(self.document_availability_url, data, **self.exporter_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Given no_document_comments
        data = {"is_document_available": "no", "no_document_comments": "yada yada yada"}
        response = self.client.post(self.document_availability_url, data, **self.exporter_headers)
        assert response.status_code == status.HTTP_200_OK

    @parameterized.expand([[{"is_document_sensitive": "yes"}], [{"is_document_sensitive": "no"}]])
    def test_document_sensitive(self, data):
        response = self.client.post(self.document_sensitivity_url, data, **self.exporter_headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue("good" in response.json())

    def test_document_sensitivity_empty_failure(self):
        data = {"is_document_sensitive": None}
        response = self.client.post(self.document_sensitivity_url, data, **self.exporter_headers)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        errors = response.json()["errors"]
        self.assertTrue("is_document_sensitive" in errors)
        self.assertEqual(errors["is_document_sensitive"][0], "Select yes or no")
