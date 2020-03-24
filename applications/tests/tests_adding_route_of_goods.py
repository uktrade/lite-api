from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.enums import CaseTypeEnum, CaseTypeSubTypeEnum
from test_helpers.clients import DataTestClient


class AddingRouteOfGoodsTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_standard_application(self.organisation)
        self.url = reverse("applications:route_of_goods", kwargs={"pk": self.draft.id})

        self.data = {"is_shipped_waybill_or_lading": "True"}

    @parameterized.expand([[CaseTypeEnum.F680], [CaseTypeEnum.EXHIBITION], [CaseTypeEnum.GIFTING]])
    def test_action_cannot_be_performed_on_non_open_or_standard_applications(self, case_type):
        case = self.create_mod_clearance_application(self.organisation, case_type=case_type)
        url = reverse("applications:route_of_goods", kwargs={"pk": case.id})
        response = self.client.put(url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"], ["This operation can only be used on applications of type: open, standard"]
        )

    @parameterized.expand([CaseTypeSubTypeEnum.OPEN, CaseTypeSubTypeEnum.STANDARD])
    def test_action_can_be_performed_on_standard_application(self, case_type):
        if case_type == CaseTypeSubTypeEnum.OPEN:
            case = self.create_draft_open_application(self.organisation)
        else:
            case = self.create_draft_standard_application(self.organisation)

        url = reverse("applications:route_of_goods", kwargs={"pk": case.id})
        response = self.client.put(url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case.refresh_from_db()
        self.assertTrue(case.is_shipped_waybill_or_lading)
        self.assertEqual(case.non_waybill_or_lading_route_details, None)


    def test_can_(self, case_type):
        if case_type == CaseTypeSubTypeEnum.OPEN:
            case = self.create_draft_open_application(self.organisation)
        else:
            case = self.create_draft_standard_application(self.organisation)

        url = reverse("applications:route_of_goods", kwargs={"pk": case.id})
        response = self.client.put(url, self.data, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case.refresh_from_db()
        self.assertTrue(case.is_shipped_waybill_or_lading)
        self.assertEqual(case.non_waybill_or_lading_route_details, None)
