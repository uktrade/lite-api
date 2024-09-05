from rest_framework import status
from rest_framework.reverse import reverse

from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.control_list_entries.factories import ControlListEntriesFactory
from test_helpers.clients import DataTestClient


class ControlListEntriesListTests(DataTestClient):
    def setUp(self):
        self.url = reverse("exporter_staticdata:control_list_entries:control_list_entries")
        super().setUp()

    def test_list_view_success(self):
        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(len(response.json()) > 0)

        for cle in response.json():
            self.assertEqual(list(cle.keys()), ["rating", "text"])

    def test_list_view_failure_bad_headers(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_view_success_exact_response(self):
        # Set up empty CLE db table for this test only
        ControlListEntry.objects.all().delete()

        cle_1 = ControlListEntriesFactory(rating="ABC123", controlled=True)
        cle_2 = ControlListEntriesFactory(rating="1Z101", controlled=True)
        cle_3 = ControlListEntriesFactory(rating="ZXYW", controlled=True)

        response = self.client.get(self.url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.json(),
            [
                {"rating": cle_1.rating, "text": cle_1.text},
                {"rating": cle_2.rating, "text": cle_2.text},
                {"rating": cle_3.rating, "text": cle_3.text},
            ],
        )
