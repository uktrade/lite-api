from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class ControlListEntriesListTests(DataTestClient):
    def setUp(self):
        self.url = reverse("exporter_staticdata:control_list_entries:control_list_entries")
        super().setUp()

    def test_list_view_success(self):
        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for cle in response.json():
            self.assertEqual(list(cle.keys()), ["rating", "text"])

    def test_list_view_failure_bad_headers(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
