from rest_framework import status
from rest_framework.reverse import reverse

from api.cases.enums import CaseTypeEnum
from test_helpers.clients import DataTestClient
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class CaseTypesTests(DataTestClient):
    def test_get_case_types_success(self):
        url = reverse("static:case_types:case_types")

        response = self.client.get(url, **self.exporter_headers)
        response_data = response.json()["case_types"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(CaseTypeEnum.CASE_TYPE_LIST))
        for case_type in CaseTypeEnum.CASE_TYPE_LIST:
            self.assertIn(case_type.reference, str(response_data))


class CaseTypesResponseTests(EndPointTests):
    url = "/static/case-types/"

    def test_case_types(self):
        self.call_endpoint(self.get_exporter_headers(), self.url)
