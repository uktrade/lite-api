from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class StatusesTests(DataTestClient):

    url = reverse("static:statuses:case_statuses")

    def test_get_statuses(self):
        response = self.client.get(self.url, **self.exporter_headers)
        data = response.json()["statuses"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", data[0])
        self.assertEqual(data[0]["priority"], 1)
        self.assertEqual(data[0]["key"], "submitted")
        self.assertEqual(data[0]["value"], "Submitted")


class StatusesResponseTests(EndPointTests):
    url = "/static/statuses/"

    def test_statuses(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)
