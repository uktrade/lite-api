from rest_framework import status
from rest_framework.reverse import reverse

from goods.enums import GoodPvGraded, GoodControlled
from goods.models import Good, PvGradingDetails
from test_helpers.clients import DataTestClient


class GoodsEditUnsubmittedGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.good = self.create_good(description="This is a good", org=self.organisation)
        self.url = reverse("goods:good", kwargs={"pk": str(self.good.id)})

    def test_edit_good_clc_is_good_controlled_returns_200_ok_response(self):
        request_data = {"is_good_controlled": GoodControlled.NO}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.json()["good"]["is_good_controlled"]["key"], GoodControlled.NO)
        self.assertEquals(Good.objects.all().count(), 1)

    def test_edit_good_clc_control_code_returns_200_ok_response(self):
        request_data = {"is_good_controlled": GoodControlled.YES, "control_code": "ML1a"}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.json()["good"]["control_code"], "ML1a")
        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_editing_good_pv_grading_is_pv_graded_to_no_then_pv_grading_details_is_deleted(self):
        request_data = {"is_pv_graded": GoodPvGraded.NO}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.json()["good"]["is_pv_graded"]["key"], GoodPvGraded.NO)
        self.assertEquals(response.json()["good"]["pv_grading_details"], None)
        self.assertEquals(Good.objects.all().count(), 1)
        self.assertEquals(PvGradingDetails.objects.all().count(), 0)

    def test_edit_good_pv_grading_details_returns_200_ok_response(self):
        pv_grading_details = self.good.pv_grading_details.__dict__
        pv_grading_details.pop("_state")
        pv_grading_details.pop("id")
        pv_grading_details["date_of_issue"] = "2020-01-01"
        request_data = {"is_pv_graded": GoodPvGraded.YES, "pv_grading_details": pv_grading_details}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.json()["good"]["pv_grading_details"]["date_of_issue"], "2020-01-01")
        self.assertEquals(Good.objects.all().count(), 1)
