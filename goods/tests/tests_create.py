from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from goods.enums import GoodControlled
from test_helpers.clients import DataTestClient


class GoodsCreateTests(DataTestClient):

    url = reverse("goods:goods")

    @parameterized.expand(
        [
            ("Widget", GoodControlled.YES, "ML1a", True, "1337",),  # Create a new good successfully
            ("Widget", GoodControlled.NO, None, True, "1337",),  # Control List Entry shouldn't be set
            ("Test Unsure Good Name", GoodControlled.UNSURE, None, True, "1337",),  # CLC query
        ]
    )
    def test_create_good(
        self, description, is_good_controlled, control_code, is_good_end_product, part_number,
    ):
        data = {
            "description": description,
            "is_good_controlled": is_good_controlled,
            "control_code": control_code,
            "is_good_end_product": is_good_end_product,
            "part_number": part_number,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()["good"]

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(response_data["description"], description)
        self.assertEquals(response_data["is_good_controlled"], is_good_controlled)
        self.assertEquals(response_data["control_code"], control_code)
        self.assertEquals(response_data["is_good_end_product"], is_good_end_product)
        self.assertEquals(response_data["part_number"], part_number)

    @parameterized.expand(
        [
            ("Widget", GoodControlled.YES, "", True, "1337",),  # Controlled but is missing control list entry
            ("Widget", GoodControlled.YES, "invalid", True, "1337",),  # Controlled but has invalid control list entry
        ]
    )
    def test_create_good_failure(
        self, description, is_good_controlled, control_code, is_good_end_product, part_number,
    ):
        data = {
            "description": description,
            "is_good_controlled": is_good_controlled,
            "control_code": control_code,
            "is_good_end_product": is_good_end_product,
            "part_number": part_number,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid control list entry", str(response_data))

    # This data is the first successful created good in the test above, if both tests fail it may be related to that
    # data being incorrect now
    @parameterized.expand(
        [
            ("Widget", GoodControlled.YES, "ML1a", True, "1337", True),
            ("Widget", GoodControlled.YES, "ML1a", True, "1337", False),
        ]
    )
    def test_create_validate_only(
        self, description, is_good_controlled, control_code, is_good_end_product, part_number, validate_only,
    ):
        data = {
            "description": description,
            "is_good_controlled": is_good_controlled,
            "control_code": control_code,
            "is_good_end_product": is_good_end_product,
            "part_number": part_number,
            "validate_only": validate_only,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        if validate_only:
            self.assertEquals(response.status_code, status.HTTP_200_OK)
        else:
            self.assertEquals(response.status_code, status.HTTP_201_CREATED)
