from django.urls import reverse
from rest_framework import status

from lite_content.lite_api.goods import Good
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
        self.assertEquals(errors["missing_document_reason"][0], Good.INVALID_MISSING_DOCUMENT_REASON)

    def test_missing_document_reason_valid_success(self):
        data = {"has_document_to_upload": "no", "missing_document_reason": GoodMissingDocumentReasons.OFFICIAL_SENSITIVE}
        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        good = response.json()["good"]
        self.assertEquals(good["missing_document_reason"], GoodMissingDocumentReasons.OFFICIAL_SENSITIVE)
