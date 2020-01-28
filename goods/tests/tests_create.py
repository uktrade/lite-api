import uuid

from copy import deepcopy
from rest_framework import status
from rest_framework.reverse import reverse

from goods.enums import GoodControlled, GoodPvGraded, PvGrading, GoodStatus
from goods.models import Good
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient
from test_helpers.helpers import is_not_verified_flag_set_on_good

URL = reverse("goods:goods")

REQUEST_DATA = {
    "description": f"Plastic bag {uuid.uuid4()}",
    "is_good_controlled": GoodControlled.NO,
    "control_code": None,
    "part_number": "1337",
    "validate_only": False,
    "is_pv_graded": GoodPvGraded.NO,
    "pv_grading_details": {
        "grading": None,
        "custom_grading": "Custom Grading",
        "prefix": "Prefix",
        "suffix": "Suffix",
        "issuing_authority": "Issuing Authority",
        "reference": "ref123",
        "date_of_issue": "2019-12-25",
    },
}


def _assert_response_data(self, response_data, request_data):
    self.assertEquals(response_data["description"], request_data["description"])
    self.assertEquals(response_data["part_number"], request_data["part_number"])
    self.assertEquals(response_data["status"]["key"], GoodStatus.DRAFT)

    if request_data["is_good_controlled"] == GoodControlled.YES:
        self.assertEquals(response_data["is_good_controlled"]["key"], GoodControlled.YES)
        self.assertEquals(response_data["control_code"], request_data["control_code"])

    if request_data["is_pv_graded"] == GoodPvGraded.YES:
        self.assertEquals(response_data["is_pv_graded"]["key"], GoodPvGraded.YES)

        response_data_pv_grading_details = response_data["pv_grading_details"]
        request_data_pv_grading_details = request_data["pv_grading_details"]

        if request_data_pv_grading_details["grading"]:
            grading_response = response_data_pv_grading_details.pop("grading")
            grading_request = request_data_pv_grading_details.pop("grading")
            self.assertEquals(grading_response["key"], grading_request)

        for key, value in request_data_pv_grading_details.items():
            self.assertEqual(response_data_pv_grading_details[key], value)


class GoodsCreateGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.request_data = deepcopy(REQUEST_DATA)

    def test_when_creating_a_good_with_not_controlled_and_not_pv_graded_then_created_response_is_returned(self):
        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEquals(Good.objects.all().count(), 1)
        self.assertTrue(is_not_verified_flag_set_on_good(Good.objects.first()))

    def test_when_creating_a_good_with_pv_graded_and_controlled_then_created_response_is_returned(self):
        self.request_data["is_good_controlled"] = GoodControlled.YES
        self.request_data["control_code"] = "ML1a"
        self.request_data["is_pv_graded"] = GoodPvGraded.YES

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEquals(Good.objects.all().count(), 1)
        self.assertTrue(is_not_verified_flag_set_on_good(Good.objects.first()))

    def test_when_creating_a_good_with_good_controlled_set_to_null_then_bad_request_response_is_returned(self):
        self.request_data["is_good_controlled"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"is_good_controlled": ["This field may not be null."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_pv_graded_set_to_null_then_bad_request_response_is_returned(self):
        self.request_data["is_pv_graded"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"is_pv_graded": ["This field may not be null."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_validate_only_then_ok_response_is_returned_and_good_is_not_created(self,):
        self.request_data["is_good_controlled"] = GoodControlled.NO
        self.request_data["is_pv_graded"] = GoodPvGraded.NO
        self.request_data["validate_only"] = True

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(Good.objects.all().count(), 0)


class GoodsCreateControlledGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.request_data = deepcopy(REQUEST_DATA)

    def test_when_creating_a_good_with_all_fields_then_created_response_is_returned(self):
        self.request_data["is_good_controlled"] = GoodControlled.YES
        self.request_data["control_code"] = "ML1a"

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEquals(Good.objects.all().count(), 1)
        self.assertTrue(is_not_verified_flag_set_on_good(Good.objects.first()))

    def test_when_creating_a_good_with_a_null_control_code_then_bad_request_response_is_returned(self):
        self.request_data["is_good_controlled"] = GoodControlled.YES

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(response.json()["errors"], {"control_code": ["This field may not be null."]})
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_an_invalid_control_code_then_bad_request_response_is_returned(self):
        self.request_data["is_good_controlled"] = GoodControlled.YES
        self.request_data["control_code"] = "invalid"

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(response.json()["errors"], {"control_code": ["Enter a valid control list entry"]})
        self.assertEquals(Good.objects.all().count(), 0)


class GoodsCreatePvGradedGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.request_data = deepcopy(REQUEST_DATA)

    def test_when_creating_a_good_with_a_custom_grading_then_created_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEquals(Good.objects.all().count(), 1)
        self.assertTrue(is_not_verified_flag_set_on_good(Good.objects.first()))

    def test_when_creating_a_good_with_a_grading_then_created_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["custom_grading"] = None
        self.request_data["pv_grading_details"]["grading"] = PvGrading.UK_OFFICIAL

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], self.request_data)
        self.assertEquals(Good.objects.all().count(), 1)
        self.assertTrue(is_not_verified_flag_set_on_good(Good.objects.first()))

    def test_when_creating_a_good_with_a_null_grading_and_custom_grading_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["custom_grading"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"custom_grading": [strings.Goods.NO_CUSTOM_GRADING_ERROR]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_a_grading_and_custom_grading_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["grading"] = PvGrading.UK_OFFICIAL
        self.request_data["pv_grading_details"]["custom_grading"] = "Custom Grading"

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"custom_grading": [strings.Goods.PROVIDE_ONLY_GRADING_OR_CUSTOM_GRADING_ERROR]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_a_null_authority_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["issuing_authority"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"issuing_authority": ["This field may not be null."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_a_null_reference_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["reference"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"reference": ["This field may not be null."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_when_creating_a_good_with_a_null_date_of_issue_then_bad_response_is_returned(self):
        self.request_data["is_pv_graded"] = GoodPvGraded.YES
        self.request_data["pv_grading_details"]["date_of_issue"] = None

        response = self.client.post(URL, self.request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"date_of_issue": ["This field may not be null."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)
