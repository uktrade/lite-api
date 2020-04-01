from rest_framework import status
from rest_framework.reverse import reverse

from cases.enums import CaseTypeEnum
from test_helpers.clients import DataTestClient
from test_helpers.test_endpoints.test_endpoint_response_time import EndPointTests


class CaseTypesTests(DataTestClient):
    def test_get_case_types_success(self):
        url = reverse("static:case_types:case_types")

        response = self.client.get(url)
        response_data = response.json()["case_types"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(CaseTypeEnum.case_type_list))
        for case_type in CaseTypeEnum.case_type_list:
            self.assertIn(case_type.reference, str(response_data))


class CaseTypesResponseTests(EndPointTests):
    url = "/static/case-types/"

    def test_case_types(self):
        self.call_endpoint(self.get_exporter(), self.url)
