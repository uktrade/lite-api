from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient


class MTCREntriesTests(DataTestClient):
    def test_view(self):
        url = reverse("staticdata:regimes:mtcr_entries")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "entries": [
                    ["MTCR1", "MTCR1"],
                ],
            },
        )
