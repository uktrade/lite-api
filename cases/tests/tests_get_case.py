from django.urls import reverse
from rest_framework import status

from applications.models import PartyOnApplication
from parties.enums import PartyType
from test_helpers.clients import DataTestClient


class CaseGetTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)

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
            response_data["case"]["application"]["third_parties"][0]
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
