from rest_framework import status
from rest_framework.reverse import reverse

from api.cases.enums import AdviceType
from test_helpers.clients import DataTestClient
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class DecisionsTests(DataTestClient):
    def test_get_decisions_success(self):
        url = reverse("staticdata:decisions:decisions")

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["decisions"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(AdviceType.choices))
        for decision in AdviceType.choices:
            self.assertIn(decision[0], str(response_data))


class DecisionsResponseTests(EndPointTests):
    url = "/static/decisions/"

    def test_decisions(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)
