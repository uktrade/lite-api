from rest_framework import status
from rest_framework.reverse import reverse

from api.goods.enums import PvGrading
from test_helpers.clients import DataTestClient
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class PrivateVentureGradingsTests(DataTestClient):
    def test_get_all_private_venture_gradings(self):
        url = reverse("static:private_venture_gradings:private_venture_gradings")
        response = self.client.get(url, **self.exporter_headers)
        gradings = response.json()["pv_gradings"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for choice in PvGrading.choices:
            self.assertIn({choice[0]: choice[1]}, gradings)

    def test_get_gov_private_venture_gradings(self):
        url = reverse("static:private_venture_gradings:gov_private_venture_gradings")
        response = self.client.get(url, **self.exporter_headers)
        gradings = response.json()["pv_gradings"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for choice in PvGrading.gov_choices:
            self.assertIn({choice[0]: choice[1]}, gradings)


class PrivateVentureGradingsResponseTests(EndPointTests):
    url = "/static/private-venture-gradings/"

    def test_private_venture_gradings(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)
