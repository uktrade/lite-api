from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class ExporterControlListEntriesListTests(DataTestClient):
    def setUp(self):
        self.url = reverse("staticdata:control_list_entries:exporter_list")
        super().setUp()

    def test_exporter_list_view_success(self):
        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(list(response.json().keys()), ["control_list_entries"])

        for cle in response.json()["control_list_entries"]:
            self.assertEqual(list(cle.keys()), ["rating", "text"])

    def test_exporter_list_view_failure_bad_headers(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
