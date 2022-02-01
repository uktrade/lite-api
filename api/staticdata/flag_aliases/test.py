from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class FlagAliasesTests(DataTestClient):

    url = reverse("staticdata:flag_aliases:flag_aliases")

    def test_get_flag_aliases(self):
        response = self.client.get(self.url, **self.exporter_headers)
        denial_reasons = response.json()["queue_data"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(len(denial_reasons), 0)


class FlagAliasesResponseTests(EndPointTests):
    url = "/static/flag_aliases/"

    def test_denial_reasons(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)
