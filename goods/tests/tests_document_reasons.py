from unittest import mock

from django.urls import reverse
from rest_framework import status

from lite_content.lite_api.strings import Goods
from static.missing_document_reasons.enums import GoodMissingDocumentReasons
from test_helpers.clients import DataTestClient


class GoodDocumentMissingReasonsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.good = self.create_controlled_good("a good", self.organisation)
        self.url = reverse("goods:good_document_sensitivity", kwargs={"pk": self.good.id})

    def test_has_document_to_upload_yes_success(self):
        data = {"has_document_to_upload": "yes"}
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertTrue("good" in response.json())

    def test_missing_document_reason_empty_failure(self):
        data = {"has_document_to_upload": "no", "missing_document_reason": "blank"}
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
        errors = response.json()["errors"]
        self.assertTrue("missing_document_reason" in errors)
        self.assertEquals(errors["missing_document_reason"][0], Goods.INVALID_MISSING_DOCUMENT_REASON)

    def test_missing_document_reason_valid_success(self):
        data = {
            "has_document_to_upload": "no",
            "missing_document_reason": GoodMissingDocumentReasons.OFFICIAL_SENSITIVE,
        }
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        good = response.json()["good"]
        self.assertEquals(good["missing_document_reason"], GoodMissingDocumentReasons.OFFICIAL_SENSITIVE)

    @mock.patch("documents.tasks.prepare_document.now")
    def test_uploading_document_clears_missing_document_reason(self, prepare_document_function):
        # Give a missing document reason
        data = {
            "has_document_to_upload": "no",
            "missing_document_reason": GoodMissingDocumentReasons.NO_DOCUMENT,
        }
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertTrue(response.json()["good"]["missing_document_reason"])

        # Upload a document for the good
        data = [
            {"name": "file123.pdf", "s3_key": "file123_12345678.pdf", "size": 476, "description": "Description 58398"}
        ]
        url = reverse("goods:documents", kwargs={"pk": self.good.id})
        response = self.client.post(url, data=data, **self.exporter_headers)

        self.assertEquals(status.HTTP_201_CREATED, response.status_code)

        # Get good and check the missing document reason is removed
        url = reverse("goods:good", kwargs={"pk": self.good.id})
        response = self.client.get(url, **self.exporter_headers)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertFalse(response.json()["good"]["missing_document_reason"])
