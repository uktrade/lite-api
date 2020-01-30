from rest_framework import status
from rest_framework.reverse import reverse

from goods.enums import PvGrading
from test_helpers.clients import DataTestClient


class PrivateVentureGradingsTests(DataTestClient):
    def test_get_all_private_venture_gradings(self):
        url = reverse("static:private_venture_gradings:private_venture_gradings")
        response = self.client.get(url)
        gradings = response.json()["pv_gradings"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(gradings), len(PvGrading.choices))

    def test_get_gov_private_venture_gradings(self):
        url = reverse("static:private_venture_gradings:gov_private_venture_gradings")
        response = self.client.get(url)
        gradings = response.json()["pv_gradings"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(gradings), len(PvGrading.gov_choices))
