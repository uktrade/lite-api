from django.urls import reverse
from rest_framework import status

from lite_content.lite_api import strings
from test_helpers.clients import DataTestClient


class AddingRouteOfGoodsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_standard_application(self.organisation)
        self.url = reverse("applications:route_of_goods", kwargs={"pk": self.draft.id})

        self.is_shipped_waybill_or_lading_field = "is_shipped_waybill_or_lading"
        self.non_waybill_or_lading_route_details_field = "non_waybill_or_lading_route_details"
        self.data = {self.is_shipped_waybill_or_lading_field: "True"}

    def test_edit_standard_applications_success(self):
        draft = self.create_draft_standard_application(self.organisation)

        url = reverse("applications:route_of_goods", kwargs={"pk": draft.id})
        response = self.client.put(url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        draft.refresh_from_db()
        self.assertTrue(draft.is_shipped_waybill_or_lading)
        self.assertEqual(draft.non_waybill_or_lading_route_details, None)

    def test_edit_answered_no_but_no_details_given_failure(self):
        data = {self.is_shipped_waybill_or_lading_field: "False"}
        draft = self.create_draft_standard_application(self.organisation)
        url = reverse("applications:route_of_goods", kwargs={"pk": draft.id})

        response = self.client.put(url, data, **self.exporter_headers)

        draft.refresh_from_db()
        response_errors = response.json()["errors"]

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(draft.is_shipped_waybill_or_lading, True)
        self.assertEqual(draft.non_waybill_or_lading_route_details, None)
        self.assertEqual(len(response_errors), 1)
        self.assertEqual(
            response_errors[self.non_waybill_or_lading_route_details_field],
            [strings.Applications.Generic.RouteOfGoods.SHIPPING_DETAILS],
        )

    def test_edit_no_answer_given_failure(self):
        data = {self.is_shipped_waybill_or_lading_field: None}

        response = self.client.put(self.url, data, **self.exporter_headers)

        response_errors = response.json()["errors"]
        self.draft.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.draft.is_shipped_waybill_or_lading, True)
        self.assertEqual(len(response_errors), 1)
        self.assertEqual(
            response_errors[self.is_shipped_waybill_or_lading_field],
            [strings.Applications.Generic.RouteOfGoods.IS_SHIPPED_AIR_WAY_BILL_OR_LADING],
        )

    def test_edit_answered_no_and_details_given_success(self):
        shipping_details = "It's not shipped that way."
        data = {
            self.is_shipped_waybill_or_lading_field: "False",
            self.non_waybill_or_lading_route_details_field: shipping_details,
        }

        response = self.client.put(self.url, data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.is_shipped_waybill_or_lading, False)
        self.assertEqual(self.draft.non_waybill_or_lading_route_details, shipping_details)

    def test_edit_when_application_not_major_editable_failure(self):
        # Submit to change status from `draft` to `submitted
        self.submit_application(self.draft)

        response = self.client.put(self.url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["non_field_errors"],
            [strings.Applications.Generic.INVALID_OPERATION_FOR_NON_DRAFT_OR_MAJOR_EDIT_CASE_ERROR],
        )
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.is_shipped_waybill_or_lading, True)
        self.assertEqual(self.draft.non_waybill_or_lading_route_details, None)
