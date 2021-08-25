from django.urls import reverse
from rest_framework import status
from urllib import parse

from test_helpers.clients import DataTestClient


class DataWorkspaceExternalDataViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        test_host = "http://testserver"
        self.denial_external_data = parse.urljoin(test_host, reverse("data_workspace:dw-external-data-denial"))

    def test_denial_view(self):
        response = self.client.options(self.denial_external_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_keys = response.json()["actions"]["GET"].keys()
        expected_keys = (
            "id",
            "goodonexternal_data",
            "controllistentry",
        )
        self.assertEqual(tuple(actual_keys), expected_keys)
