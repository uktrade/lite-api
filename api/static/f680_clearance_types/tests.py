from rest_framework import status
from rest_framework.reverse import reverse

from api.static.f680_clearance_types.enums import F680ClearanceTypeEnum
from test_helpers.clients import DataTestClient
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class F680ClearanceTypesTests(DataTestClient):
    def test_get_f680_clearance_types_success(self):
        url = reverse("static:f680_clearance_types:f680_clearance_types")

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["types"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(F680ClearanceTypeEnum.choices))

        for choice in F680ClearanceTypeEnum.choices:
            self.assertIn(choice[0], str(response_data))


class F680ClearanceTypesResponseTests(EndPointTests):
    url = "/static/f680-clearance-types/"

    def test_F680_clearance_types(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)
