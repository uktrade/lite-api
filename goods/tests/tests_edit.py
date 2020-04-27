from rest_framework import status
from rest_framework.reverse import reverse

from goods.enums import GoodPvGraded, GoodControlled, PvGrading
from goods.models import Good, PvGradingDetails
from goods.tests.factories import GoodFactory
from static.control_list_entries.helpers import get_control_list_entry
from static.control_list_entries.models import ControlListEntry
from test_helpers.clients import DataTestClient


class GoodsEditUnsubmittedGoodTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.good = self.create_good(description="This is a good", organisation=self.organisation)
        self.url = reverse("goods:good", kwargs={"pk": str(self.good.id)})

    def test_when_updating_is_good_controlled_to_no_then_control_list_entries_is_deleted(self):
        request_data = {"is_good_controlled": GoodControlled.NO}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.json()["good"]["is_good_controlled"]["key"], GoodControlled.NO)
        self.assertEquals(response.json()["good"]["control_list_entries"], [])

        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_updating_clc_control_list_entries_then_new_control_list_entries_is_returned(self):
        ControlListEntry.create("ML1b", "Info here", None, False)
        request_data = {"is_good_controlled": GoodControlled.YES, "control_list_entries": ["ML1a", "ML1b"]}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(
            response.json()["good"]["control_list_entries"],
            [
                {"rating": "ML1a", "text": get_control_list_entry("ML1a").text},
                {"rating": "ML1b", "text": get_control_list_entry("ML1b").text},
            ],
        )
        self.assertEquals(Good.objects.all().count(), 1)

    def test_when_removing_a_clc_control_list_entry_from_many_then_new_control_list_entries_is_returned(self):
        ControlListEntry.create("ML1b", "Info here", None, False)
        good = GoodFactory(
            organisation=self.organisation, is_good_controlled=GoodControlled.YES, control_list_entries=["ML1a", "ML1b"]
        )
        url = reverse("goods:good", kwargs={"pk": str(good.id)})

        request_data = {"is_good_controlled": GoodControlled.YES, "control_list_entries": ["ML1b"]}

        response = self.client.put(url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(
            response.json()["good"]["control_list_entries"],
            [{"rating": "ML1b", "text": get_control_list_entry("ML1b").text}],
        )

    def test_when_updating_is_pv_graded_to_no_then_pv_grading_details_are_deleted(self):
        request_data = {"is_pv_graded": GoodPvGraded.NO}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.json()["good"]["is_pv_graded"]["key"], GoodPvGraded.NO)
        self.assertEquals(response.json()["good"]["pv_grading_details"], None)
        self.assertEquals(Good.objects.all().count(), 1)
        self.assertEquals(PvGradingDetails.objects.all().count(), 0)

    def test_when_updating_pv_grading_details_then_new_details_are_returned(self):
        pv_grading_details = self.good.pv_grading_details.__dict__
        pv_grading_details.pop("_state")
        pv_grading_details.pop("id")
        pv_grading_details["grading"] = PvGrading.UK_OFFICIAL
        pv_grading_details["custom_grading"] = None
        pv_grading_details["date_of_issue"] = "2020-01-01"
        request_data = {"is_pv_graded": GoodPvGraded.YES, "pv_grading_details": pv_grading_details}

        response = self.client.put(self.url, request_data, **self.exporter_headers)

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.json()["good"]["pv_grading_details"]["date_of_issue"], "2020-01-01")
        self.assertEquals(response.json()["good"]["pv_grading_details"]["grading"]["key"], PvGrading.UK_OFFICIAL)
        self.assertEquals(response.json()["good"]["pv_grading_details"]["custom_grading"], None)
        self.assertEquals(Good.objects.all().count(), 1)
