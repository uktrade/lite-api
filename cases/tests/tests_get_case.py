from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from cases.enums import CaseTypeEnum
from flags.enums import SystemFlags
from flags.models import Flag
from static.trade_control.enums import TradeControlActivity, TradeControlProductCategory
from test_helpers.clients import DataTestClient


class CaseGetTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)

    def test_case_returns_expected_third_party(self):
        """
        Given a case with a third party exists
        When the case is retrieved
        Then the third party is present in the json data
        """
        case = self.submit_application(self.standard_application)
        url = reverse("cases:case", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)

        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._assert_party(
            self.standard_application.third_parties.last().party,
            response_data["case"]["application"]["third_parties"][0],
        )
        self._assert_party(self.standard_application.consignee.party, response_data["case"]["application"]["consignee"])

    def _assert_party(self, expected, actual):
        self.assertEqual(str(expected.id), actual["id"])
        self.assertEqual(str(expected.name), actual["name"])
        self.assertEqual(str(expected.country.name), actual["country"]["name"])
        self.assertEqual(str(expected.website), actual["website"])
        self.assertEqual(str(expected.type), actual["type"])
        self.assertEqual(str(expected.organisation.id), actual["organisation"])

        sub_type = actual["sub_type"]
        # sub_type is not always a dict.
        self.assertEqual(
            str(expected.sub_type), sub_type["key"] if isinstance(sub_type, dict) else sub_type,
        )

    def test_case_returns_expected_goods_flags(self):
        case = self.submit_application(self.standard_application)
        url = reverse("cases:case", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_flags = [Flag.objects.get(id=SystemFlags.GOOD_NOT_YET_VERIFIED_ID).name]
        actual_flags_on_case = [flag["name"] for flag in response_data["case"]["all_flags"]]
        actual_flags_on_goods = [flag["name"] for flag in response_data["case"]["application"]["goods"][0]["flags"]]

        self.assertIn(actual_flags_on_case[0], expected_flags)
        self.assertEqual(actual_flags_on_goods, expected_flags)

    def test_case_returns_expected_goods_types_flags(self):
        self.open_application = self.create_draft_open_application(self.organisation)
        self.open_case = self.submit_application(self.open_application)
        self.open_case_url = reverse("cases:case", kwargs={"pk": self.open_case.id})

        response = self.client.get(self.open_case_url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_flags = [Flag.objects.get(id=SystemFlags.GOOD_NOT_YET_VERIFIED_ID).name]
        actual_flags_on_case = [flag["name"] for flag in response_data["case"]["all_flags"]]
        actual_flags_on_goods_type = [
            flag["name"] for flag in response_data["case"]["application"]["goods_types"][0]["flags"]
        ]

        self.assertIn(actual_flags_on_case[0], expected_flags)
        self.assertEqual(actual_flags_on_goods_type, expected_flags)

    def test_case_returns_has_advice(self):
        case = self.submit_application(self.standard_application)
        url = reverse("cases:case", kwargs={"pk": case.id})

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        has_advice_response_data = response.json()["case"]["has_advice"]
        self.assertIn("user", has_advice_response_data)
        self.assertIn("my_user", has_advice_response_data)
        self.assertIn("team", has_advice_response_data)
        self.assertIn("my_team", has_advice_response_data)
        self.assertIn("final", has_advice_response_data)

    @parameterized.expand(
        [
            (CaseTypeEnum.SICL.id, DataTestClient.create_draft_standard_application),
            (CaseTypeEnum.OICL.id, DataTestClient.create_draft_open_application),
        ]
    )
    def test_trade_control_case(self, case_type_id, create_function):
        application = create_function(self, self.organisation, case_type_id=case_type_id)
        application.trade_control_activity = TradeControlActivity.OTHER
        application.trade_control_activity_other = "other activity"
        application.trade_control_product_categories = [key for key, _ in TradeControlProductCategory.choices]
        case = self.submit_application(application)

        url = reverse("cases:case", kwargs={"pk": case.id})
        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case_application = response.json()["case"]["application"]

        trade_control_activity = case_application["trade_control_activity"]["value"]
        self.assertEqual(trade_control_activity, case.trade_control_activity_other)

        trade_control_product_categories = [
            category["key"] for category in case_application["trade_control_product_categories"]
        ]
        self.assertEqual(trade_control_product_categories, case.trade_control_product_categories)
