import uuid

from parameterized import parameterized
from rest_framework import status
from rest_framework.reverse import reverse

from goods.enums import GoodControlled, GoodPVGraded, PVGrading
from goods.models import Good
from test_helpers.clients import DataTestClient
from test_helpers.decorators import none_param_tester


class GoodsCreateTests(DataTestClient):
    url = reverse("goods:goods")

    @parameterized.expand(
        [
            ("Widget", GoodControlled.YES, "ML1a", "1337",),  # Create a new good successfully
            ("Widget", GoodControlled.NO, None, "1337",),  # Control List Entry shouldn't be set
            ("Test Unsure Good Name", GoodControlled.UNSURE, None, "1337",),  # CLC query
        ]
    )
    def test_create_good(
        self, description, is_good_controlled, control_code, part_number,
    ):
        data = {
            "description": description,
            "is_good_controlled": is_good_controlled,
            "control_code": control_code,
            "part_number": part_number,
            "is_pv_graded": GoodPVGraded.NO,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()["good"]
        self.assertEquals(response_data["description"], description)
        self.assertEquals(response_data["is_good_controlled"]["key"], is_good_controlled)
        self.assertEquals(response_data["control_code"], control_code)
        self.assertEquals(response_data["part_number"], part_number)
        self.assertEquals(response_data["is_pv_graded"]["key"], GoodPVGraded.NO)

    @none_param_tester("Widget", True, "ML1a", "1337")
    def test_create_good_failure(
        self, description, is_good_controlled, control_code, part_number,
    ):
        data = {
            "description": description,
            "is_good_controlled": is_good_controlled,
            "control_code": control_code,
            "part_number": part_number,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    @parameterized.expand(
        [
            ("Widget", GoodControlled.YES, "", "1337",),  # Controlled but is missing control list entry
            ("Widget", GoodControlled.YES, "invalid", "1337",),  # Controlled but has invalid control list entry
        ]
    )
    def test_create_good_control_list_entry_failure(
        self, description, is_good_controlled, control_code, part_number,
    ):
        data = {
            "description": description,
            "is_good_controlled": is_good_controlled,
            "control_code": control_code,
            "part_number": part_number,
            "is_pv_graded": GoodPVGraded.NO,
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter a valid control list entry", str(response_data))

    @parameterized.expand(
        [
            (
                # Create a new good successfully with all fields
                GoodPVGraded.YES,
                PVGrading.UK_UNCLASSIFIED,
                None,
                "prefix",
                "suffix",
                "Pv Grading Issuing Authority",
                "reference123",
                "2019-01-01",
                "Pv Grading comment",
            ),
            (
                # Custom grading needs to be present when choosing Other
                GoodPVGraded.YES,
                PVGrading.OTHER,
                "Custom grading",
                "prefix",
                "suffix",
                "Pv Grading Issuing Authority",
                "reference123",
                "2019-01-01",
                "Pv Grading comment",
            ),
            (
                # Create a new good successfully without optional fields
                GoodPVGraded.YES,
                PVGrading.UK_UNCLASSIFIED,
                None,
                None,
                None,
                "Pv Grading Issuing Authority",
                "reference123",
                "2019-01-01",
                None,
            ),
        ]
    )
    def test_create_good_with_pv_grading_returns_success(
        self,
        is_pv_graded,
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
            "is_pv_graded": is_pv_graded,
            "pv_grading_details": {
                "grading": pv_grading,
                "custom_grading": pv_grading_custom,
                "prefix": pv_grading_prefix,
                "suffix": pv_grading_suffix,
                "issuing_authority": pv_grading_issuing_authority,
                "reference": pv_grading_reference,
                "date_of_issue": pv_grading_date_of_issue,
                "comment": pv_grading_comment,
            },
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()["good"]
        self.assertEquals(response_data["description"], data.get("description"))
        self.assertEquals(response_data["is_good_controlled"]["key"], data.get("is_good_controlled"))
        self.assertEquals(response_data["is_pv_graded"]["key"], is_pv_graded)
        if is_pv_graded:
            pv_grading_details = response_data["pv_grading_details"]
            self.assertEquals(pv_grading_details["grading"]["key"], pv_grading)
            self.assertEquals(pv_grading_details["custom_grading"], pv_grading_custom)
            self.assertEquals(pv_grading_details["prefix"], pv_grading_prefix)
            self.assertEquals(pv_grading_details["suffix"], pv_grading_suffix)
            self.assertEquals(pv_grading_details["issuing_authority"], pv_grading_issuing_authority)
            self.assertEquals(pv_grading_details["reference"], pv_grading_reference)
            self.assertEquals(pv_grading_details["date_of_issue"], pv_grading_date_of_issue)
            self.assertEquals(pv_grading_details["comment"], pv_grading_comment)

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
                "Pv Grading Comment",
            ),
        ]
    )
    def test_create_good_with_pv_grading_returns_failure(
        self,
        is_pv_graded,
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
            "is_pv_graded": is_pv_graded,
            "pv_grading_details": {
                "grading": pv_grading,
                "custom_grading": pv_grading_custom,
                "prefix": pv_grading_prefix,
                "suffix": pv_grading_suffix,
                "issuing_authority": pv_grading_issuing_authority,
                "reference": pv_grading_reference,
                "date_of_issue": pv_grading_date_of_issue,
                "comment": pv_grading_comment,
            },
        }

        response = self.client.post(self.url, data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Good.objects.all().count(), 0)

    def test_create_pv_graded_good_when_grading_is_other_and_custom_grading_is_null_then_bad_response_is_returned(self):
        pass

    def test_create_good_when_validate_only_is_true_then_ok_response_is_returned_and_good_is_not_created(self):
        good_data = self._setup_good_data(
            GoodControlled.YES, "ML1a", GoodPVGraded.YES, self._setup_pv_grading_details(), validate_only=True
        )

        response = self.client.post(self.url, good_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(Good.objects.all().count(), 0)

    @staticmethod
    def _setup_good_data(
        is_good_controlled=False,
        control_code=None,
        is_pv_graded=False,
        pv_grading_details=None,
        part_number="1337",
        validate_only=False,
    ):
        return {
            "description": "Plastic bag " + str(uuid.uuid4()),
            "is_good_controlled": is_good_controlled,
            "control_code": control_code,
            "is_pv_graded": is_pv_graded,
            "pv_grading_details": pv_grading_details,
            "part_number": part_number,
            "validate_only": validate_only,
        }

    @staticmethod
    def _setup_pv_grading_details(
        grading=PVGrading.OTHER,
        custom_grading="Other",
        prefix=None,
        suffix=None,
        issuing_authority="Issuing Authority",
        reference="ref123",
        date="2019-12-25",
        comment="This is a pv graded good",
    ):
        return {
            "grading": grading,
            "custom_grading": custom_grading,
            "prefix": prefix,
            "suffix": suffix,
            "issuing_authority": issuing_authority,
            "reference": reference,
            "date_of_issue": date,
            "comment": comment,
        }
