import uuid

from rest_framework import status
from rest_framework.reverse import reverse

from goods.enums import GoodControlled, GoodPvGraded, PvGrading, GoodStatus
from goods.models import Good
from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient

url = reverse("goods:goods")


def _setup_request_data(
    is_good_controlled=GoodControlled.NO,
    control_code=None,
    is_pv_graded=GoodPvGraded.NO,
    pv_grading_details=None,
    part_number="1337",
    validate_only=False,
):
    return {
        "description": f"Plastic bag {uuid.uuid4()}",
        "is_good_controlled": is_good_controlled,
        "control_code": control_code,
        "is_pv_graded": is_pv_graded,
        "pv_grading_details": pv_grading_details,
        "part_number": part_number,
        "validate_only": validate_only,
    }


def _setup_pv_grading_details(
    grading=None,
    custom_grading="Custom Grading",
    prefix="Prefix",
    suffix="Suffix",
    issuing_authority="Issuing Authority",
    reference="ref123",
    date="2019-12-25",
):
    return {
        "grading": grading,
        "custom_grading": custom_grading,
        "prefix": prefix,
        "suffix": suffix,
        "issuing_authority": issuing_authority,
        "reference": reference,
        "date_of_issue": date,
    }


def _assert_response_data(self, response_data, request_data):
    self.assertEquals(response_data["description"], request_data["description"])
    self.assertEquals(response_data["status"]["key"], GoodStatus.DRAFT)

    if request_data["is_good_controlled"] == GoodControlled.YES:
        self.assertEquals(response_data["is_good_controlled"]["key"], request_data["is_good_controlled"])
        self.assertEquals(response_data["control_code"], request_data["control_code"])

    if request_data["is_pv_graded"] == GoodPvGraded.YES:
        self.assertEquals(response_data["is_pv_graded"]["key"], request_data["is_pv_graded"])

        pv_grading_details = response_data["pv_grading_details"]

        if request_data["pv_grading_details"]["grading"]:
            self.assertEquals(pv_grading_details["grading"]["key"], request_data["pv_grading_details"]["grading"])

        self.assertEquals(pv_grading_details["custom_grading"], request_data["pv_grading_details"]["custom_grading"])
        self.assertEquals(pv_grading_details["prefix"], request_data["pv_grading_details"]["prefix"])
        self.assertEquals(pv_grading_details["suffix"], request_data["pv_grading_details"]["suffix"])
        self.assertEquals(
            pv_grading_details["issuing_authority"], request_data["pv_grading_details"]["issuing_authority"]
        )
        self.assertEquals(pv_grading_details["reference"], request_data["pv_grading_details"]["reference"])
        self.assertEquals(pv_grading_details["date_of_issue"], request_data["pv_grading_details"]["date_of_issue"])


class GoodsCreateGoodTests(DataTestClient):
    def test_create_good_when_not_controlled_and_not_pv_graded_then_created_response_is_returned(self):
        request_data = _setup_request_data()

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], request_data)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_create_good_when_good_is_pv_graded_and_controlled_then_created_response_is_returned(self):
        request_data = _setup_request_data(
            is_good_controlled=GoodControlled.YES,
            control_code="ML1a",
            is_pv_graded=GoodPvGraded.YES,
            pv_grading_details=_setup_pv_grading_details(),
        )

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], request_data)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_create_good_when_is_good_controlled_field_is_missing_then_bad_request_response_is_returned(self):
        request_data = _setup_request_data()
        request_data.pop("is_good_controlled")

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"is_good_controlled": ["Select a value"]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_create_good_when_is_pv_graded_field_is_missing_then_bad_request_response_is_returned(self):
        request_data = _setup_request_data()
        request_data.pop("is_pv_graded")

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"is_pv_graded": ["Select a value"]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_create_good_when_validate_only_is_true_then_ok_response_is_returned_and_good_is_not_created(self):
        request_data = _setup_request_data(
            is_good_controlled=GoodControlled.NO, is_pv_graded=GoodPvGraded.NO, validate_only=True
        )

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(Good.objects.all().count(), 0)


class GoodsCreateControlledGoodTests(DataTestClient):
    def test_create_good_when_control_code_is_missing_then_bad_request_response_is_returned(self):
        request_data = _setup_request_data(is_good_controlled=GoodControlled.YES)

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(response.json()["errors"], {"control_code": ["This field may not be null."]})
        self.assertEquals(Good.objects.all().count(), 0)

    def test_create_good_when_control_code_is_invalid_then_bad_request_response_is_returned(self):
        request_data = _setup_request_data(is_good_controlled=GoodControlled.YES, control_code="invalid code")

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(response.json()["errors"], {"control_code": ["Enter a valid control list entry"]})
        self.assertEquals(Good.objects.all().count(), 0)


class GoodsCreatePvGradedGoodTests(DataTestClient):
    def test_create_good_when_all_fields_are_provided_then_created_response_is_returned(self):
        pv_grading_details = _setup_pv_grading_details()
        request_data = _setup_request_data(is_pv_graded=GoodPvGraded.YES, pv_grading_details=pv_grading_details)

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        _assert_response_data(self, response.json()["good"], request_data)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_create_good_when_grading_is_none_and_custom_grading_is_missing_then_bad_response_is_returned(self):
        pv_grading_details = _setup_pv_grading_details(custom_grading="")
        request_data = _setup_request_data(is_pv_graded=GoodPvGraded.YES, pv_grading_details=pv_grading_details)

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"custom_grading": [strings.Goods.NO_CUSTOM_GRADING_ERROR]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_create_good_when_grading_is_provided_and_custom_grading_is_provided_then_bad_response_is_returned(self):
        pv_grading_details = _setup_pv_grading_details(grading=PvGrading.UK_OFFICIAL, custom_grading="Custom Grading")
        request_data = _setup_request_data(is_pv_graded=GoodPvGraded.YES, pv_grading_details=pv_grading_details)

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"custom_grading": [strings.Goods.PROVIDE_ONLY_GRADING_OR_CUSTOM_GRADING_ERROR]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_create_good_when_authority_is_missing_then_bad_response_is_returned(self):
        pv_grading_details = _setup_pv_grading_details(issuing_authority="")
        request_data = _setup_request_data(is_pv_graded=GoodPvGraded.YES, pv_grading_details=pv_grading_details)

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"issuing_authority": ["This field may not be blank."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_create_good_when_reference_is_missing_then_bad_response_is_returned(self):
        pv_grading_details = _setup_pv_grading_details(reference="")
        request_data = _setup_request_data(is_pv_graded=GoodPvGraded.YES, pv_grading_details=pv_grading_details)

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"], {"reference": ["This field may not be blank."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)

    def test_create_good_when_date_is_missing_then_bad_response_is_returned(self):
        pv_grading_details = _setup_pv_grading_details(date="")
        request_data = _setup_request_data(is_pv_graded=GoodPvGraded.YES, pv_grading_details=pv_grading_details)

        response = self.client.post(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.json()["errors"],
            {"date_of_issue": ["Date has wrong format. Use one of these formats instead: YYYY-MM-DD."]},
        )
        self.assertEquals(Good.objects.all().count(), 0)
