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
        # entity_type is not a model field but only added in serializer hence remove it
        actual_keys.remove("entity_type")
        actual_keys = dict.fromkeys(actual_keys).keys()
        expected_keys = {
            "id",
            "created_by",
            "name",
            "address",
            "reference",
            "notifying_government",
            "country",
            "item_list_codes",
            "item_description",
            "consignee_name",
            "end_use",
            "data",
            "is_revoked",
            "is_revoked_comment",
        }
        self.assertEqual(expected_keys, actual_keys)
