import uuid

from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from goods.enums import GoodControlled, GoodPVGraded, PVGrading
from goods.models import Good
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
    def test_create_good_clc(self, description, is_good_controlled, control_code, is_good_end_product, part_number):
        data = {
            "description": description,
            "is_good_controlled": is_good_controlled,
            "control_code": control_code,
            "is_good_end_product": is_good_end_product,
            "part_number": part_number,
            "holds_pv_grading": GoodPVGraded.NO,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()["good"]
        self.assertEquals(response_data["description"], description)
        self.assertEquals(response_data["is_good_controlled"], is_good_controlled)
        self.assertEquals(response_data["control_code"], control_code)
        self.assertEquals(response_data["is_good_end_product"], is_good_end_product)
        self.assertEquals(response_data["part_number"], part_number)
        self.assertEquals(response_data["holds_pv_grading"], data.get("holds_pv_grading"))

    @parameterized.expand(
        [
            ("Widget", GoodControlled.YES, "", True, "1337",),  # Controlled but is missing control list entry
            ("Widget", GoodControlled.YES, "invalid", True, "1337",),  # Controlled but has invalid control list entry
        ]
    )
    def test_create_good_clc_failure(
        self, description, is_good_controlled, control_code, is_good_end_product, part_number,
    ):
        data = {
            "description": description,
            "is_good_controlled": is_good_controlled,
            "control_code": control_code,
            "is_good_end_product": is_good_end_product,
            "part_number": part_number,
            "holds_pv_grading": GoodPVGraded.NO,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid control list entry", str(response_data))

    @parameterized.expand(
        [
            (
                GoodPVGraded.YES,
                PVGrading.UK_UNCLASSIFIED,
                None,
                "pr3f",
                "s00f",
                "authoritah",
                "reference123",
                "2019-01-01",
                "Badget badger badger mushroom mushroom",
            ),  # Create a new good successfully with all fields
            (
                GoodPVGraded.YES,
                PVGrading.OTHER,
                "Custom grading",
                "pr3f",
                "s00f",
                "authoritah",
                "reference123",
                "2019-01-01",
                "Badget badger badger mushroom mushroom",
            ),  # Custom grading needs to be present when choosing Other
            (
                GoodPVGraded.YES,
                PVGrading.UK_UNCLASSIFIED,
                None,
                None,
                None,
                "authoritah",
                "reference123",
                "2019-01-01",
                None,
            ),  # Create a new good successfully without optional fields
        ]
    )
    def test_create_good_pv(
        self,
        holds_pv_grading,
        pv_grading,
        pv_grading_custom,
        pv_grading_prefix,
        pv_grading_suffix,
        pv_grading_issuing_authority,
        pv_grading_reference,
        pv_grading_date_of_issue,
        pv_grading_comment,
    ):
        data = {
            "description": "Plastic bag " + str(uuid.uuid4()),
            "is_good_controlled": GoodControlled.NO,
            "is_good_end_product": True,
            "holds_pv_grading": holds_pv_grading,
            "pv_grading": pv_grading,
            "pv_grading_custom": pv_grading_custom,
            "pv_grading_prefix": pv_grading_prefix,
            "pv_grading_suffix": pv_grading_suffix,
            "pv_grading_issuing_authority": pv_grading_issuing_authority,
            "pv_grading_reference": pv_grading_reference,
            "pv_grading_date_of_issue": pv_grading_date_of_issue,
            "pv_grading_comment": pv_grading_comment,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()["good"]
        self.assertEquals(response_data["description"], data.get("description"))
        self.assertEquals(response_data["is_good_controlled"], data.get("is_good_controlled"))
        self.assertEquals(response_data["is_good_end_product"], data.get("is_good_end_product"))
        self.assertEquals(response_data["holds_pv_grading"], holds_pv_grading)
        self.assertEquals(response_data["pv_grading"], pv_grading)
        self.assertEquals(response_data["pv_grading_custom"], pv_grading_custom)
        self.assertEquals(response_data["pv_grading_prefix"], pv_grading_prefix)
        self.assertEquals(response_data["pv_grading_suffix"], pv_grading_suffix)
        self.assertEquals(response_data["pv_grading_issuing_authority"], pv_grading_issuing_authority)
        self.assertEquals(response_data["pv_grading_reference"], pv_grading_reference)
        self.assertEquals(response_data["pv_grading_date_of_issue"], pv_grading_date_of_issue)
        self.assertEquals(response_data["pv_grading_comment"], pv_grading_comment)

        self.assertEquals(Good.objects.all().count(), 1)

    @parameterized.expand(
        [
            (  # Missing custom grading when main grading is other
                GoodPVGraded.YES,
                PVGrading.OTHER,
                None,
                "pr3f1x",
                "s00f1x",
                "authoritah",
                "reference123",
                "2019-01-01",
                "Badget badger badger mushroom mushroom",
            ),
            (  # Missing authority
                GoodPVGraded.YES,
                PVGrading.UK_UNCLASSIFIED,
                None,
                "pr3f1x",
                "s00f1x",
                None,
                "reference123",
                "2019-01-01",
                "Badget badger badger mushroom mushroom",
            ),
            (  # Missing reference
                GoodPVGraded.YES,
                PVGrading.UK_UNCLASSIFIED,
                None,
                "pr3f1x",
                "s00f1x",
                "authoritah",
                None,
                "2019-01-01",
                "Badget badger badger mushroom mushroom",
            ),
            (  # Missing date
                GoodPVGraded.YES,
                PVGrading.UK_UNCLASSIFIED,
                None,
                "pr3f1x",
                "s00f1x",
                "authoritah",
                "reference123",
                None,
                "Badget badger badger mushroom mushroom",
            ),
        ]
    )
    def test_create_good_pv_failure(
        self,
        holds_pv_grading,
        pv_grading,
        pv_grading_custom,
        pv_grading_prefix,
        pv_grading_suffix,
        pv_grading_issuing_authority,
        pv_grading_reference,
        pv_grading_date_of_issue,
        pv_grading_comment,
    ):
        data = {
            "description": "Plastic bag " + str(uuid.uuid4()),
            "is_good_controlled": GoodControlled.NO,
            "is_good_end_product": True,
            "holds_pv_grading": holds_pv_grading,
            "pv_grading": pv_grading,
            "pv_grading_custom": pv_grading_custom,
            "pv_grading_prefix": pv_grading_prefix,
            "pv_grading_suffix": pv_grading_suffix,
            "pv_grading_issuing_authority": pv_grading_issuing_authority,
            "pv_grading_reference": pv_grading_reference,
            "pv_grading_date_of_issue": pv_grading_date_of_issue,
            "pv_grading_comment": pv_grading_comment,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Good.objects.all().count(), 0)

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
