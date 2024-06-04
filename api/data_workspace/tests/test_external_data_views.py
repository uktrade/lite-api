from django.urls import reverse
from rest_framework import status
from urllib import parse

from test_helpers.clients import DataTestClient


class DataWorkspaceExternalDataViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        test_host = "http://testserver"
        self.denial_external_data = parse.urljoin(test_host, reverse("data_workspace:dw-external-data-denial-list"))

    def test_denial_view(self):
        response = self.client.options(self.denial_external_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_keys = response.json()["actions"]["GET"].keys()
        actual_keys = list(actual_keys)
        actual_keys = dict.fromkeys(actual_keys).keys()
        expected_keys = {
            "id",
            "created_by",
            "name",
            "regime_reg_ref",
            "address",
            "reference",
            "notifying_government",
            "country",
            "denial_cle",
            "item_description",
            "end_use",
            "is_revoked",
            "is_revoked_comment",
            "reason_for_refusal",
            "denial",
            "entity_type",
        }
        self.assertEqual(expected_keys, actual_keys)
