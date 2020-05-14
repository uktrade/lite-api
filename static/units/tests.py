from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class UnitsTests(DataTestClient):

    url = reverse("static:units:units")

    def test_get_units(self):
        response = self.client.get(self.url, **self.exporter_headers)
        units = response.json()["units"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(units["NAR"], "Number of articles")


class UnitsResponseTests(EndPointTests):
    url = "/static/units/"

    def test_units(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)
