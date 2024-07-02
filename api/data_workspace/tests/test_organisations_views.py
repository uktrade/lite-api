from django.urls import reverse
from rest_framework import status
from test_helpers.clients import DataTestClient


class OrganisationsDataWorkspaceTests(DataTestClient):

    def test_site(self):
        url = reverse("data_workspace:dw-site-response-list")
        expected_fields = {
            "id",
            "name",
            "address",
            "records_located_at",
            "users",
            "admin_users",
            "is_used_on_application",
        }

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(set(results[0].keys()), expected_fields)
