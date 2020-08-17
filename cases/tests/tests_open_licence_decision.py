from django.urls import reverse
from rest_framework import status

from cases.enums import AdviceType
from cases.tests.factories import GoodCountryDecisionFactory
from api.conf.constants import GovPermissions
from test_helpers.clients import DataTestClient


class OpenLicenceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.gov_user.role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.case = self.create_open_application_case(self.organisation)
        self.url = reverse("cases:open_licence_decision", kwargs={"pk": self.case.id})

    def test_get_approve_decision(self):
        GoodCountryDecisionFactory(case=self.case, approve=True)

        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["decision"], AdviceType.APPROVE)

    def test_get_refuse_decision(self):
        response = self.client.get(self.url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data["decision"], AdviceType.REFUSE)
