from django.urls import reverse
from rest_framework import status
from test_helpers.clients import DataTestClient


class AddressDataWorkspaceTests(DataTestClient):
    def test_addresses(self):
        url = reverse("data_workspace:dw-address-list")
        expected_fields = {"id", "address_line_1", "address_line_2", "city", "region", "postcode", "country"}

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(set(results[0].keys()), expected_fields)
