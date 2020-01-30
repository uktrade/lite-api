from django.urls import reverse
from rest_framework import status

from flags.enums import SystemFlags
from test_helpers.clients import DataTestClient


class CaseGetTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.standard_case = self.submit_application(self.standard_application)
        self.standard_case_url = reverse("cases:case", kwargs={"pk": self.standard_case.id})

    def test_case_returns_expected_third_party(self):
        """
        Given a case with a third party exists
        When the case is retrieved
        Then the third party is present in the json data
        """

        self.standard_application.third_parties.set([self.create_third_party("third party", self.organisation)])
        self.standard_application.save()

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_third_party = self.standard_application.third_parties.first()
        actual_third_party = response_data["case"]["application"]["third_parties"][0]

        self._assert_party(expected_third_party, actual_third_party)

    def test_case_returns_expected_consignee(self):
        """
        Given a case with a consignee exists
        When the case is retrieved
        Then the consignee is present in the json data
        """

        self.standard_application.consignee = self.create_consignee("consignee", self.organisation)
        self.standard_application.save()

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_consignee = self.standard_application.consignee
        actual_consignee = response_data["case"]["application"]["consignee"]

        self._assert_party(expected_consignee, actual_consignee)

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
        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_flags = [SystemFlags.GOOD_NOT_YET_VERIFIED_ID]
        actual_flags_on_case = [flag["id"] for flag in response_data["case"]["all_flags"]]
        actual_flags_on_goods = [flag["id"] for flag in response_data["case"]["application"]["goods"][0]["flags"]]

        self.assertIn(actual_flags_on_case[0], expected_flags)
        self.assertEqual(actual_flags_on_goods, expected_flags)

    def test_case_returns_expected_goods_types_flags(self):
        self.open_application = self.create_open_application(self.organisation)
        self.open_case = self.submit_application(self.open_application)
        self.open_case_url = reverse("cases:case", kwargs={"pk": self.open_case.id})

        response = self.client.get(self.open_case_url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_flags = [SystemFlags.GOOD_NOT_YET_VERIFIED_ID]
        actual_flags_on_case = [flag["id"] for flag in response_data["case"]["all_flags"]]
        actual_flags_on_goods_type = [
            flag["id"] for flag in response_data["case"]["application"]["goods_types"][0]["flags"]
        ]

        self.assertIn(actual_flags_on_case[0], expected_flags)
        self.assertEqual(actual_flags_on_goods_type, expected_flags)
