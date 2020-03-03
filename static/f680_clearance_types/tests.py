from rest_framework import status
from rest_framework.reverse import reverse

from static.f680_clearance_types.enums import F680ClearanceTypeEnum
from test_helpers.clients import DataTestClient


class F680ClearanceTypesTests(DataTestClient):
    def test_get_f680_clearance_types_success(self):
        url = reverse("static:f680_clearance_types:f680_clearance_types")

        response = self.client.get(url)
        response_data = response.json()["types"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), len(F680ClearanceTypeEnum.choices))

        for choice in F680ClearanceTypeEnum.choices:
            self.assertIn(choice[0], str(response_data))
