from rest_framework import status
from rest_framework.reverse import reverse

from cases.enums import CaseTypeExtendedEnum
from test_helpers.clients import DataTestClient


class CaseTypesTests(DataTestClient):
    def test_get_case_types_success(self):
        url = reverse("static:case_types:case_types")

        response = self.client.get(url)
        response_data = response.json()["case_types"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(CaseTypeExtendedEnum.extended_enums_list))
        for key, value in CaseTypeExtendedEnum.extended_enums_list:
            self.assertEqual(response_data[key], value)
