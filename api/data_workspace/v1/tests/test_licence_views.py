from django.urls import reverse
from rest_framework import status

from api.applications.tests.factories import GoodOnApplicationFactory
from api.cases.tests.factories import FinalAdviceFactory
from api.cases.enums import AdviceType
from api.goods.tests.factories import GoodFactory
from api.licences.tests.factories import StandardLicenceFactory, GoodOnLicenceFactory
from test_helpers.clients import DataTestClient


class DataWorkspaceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        # Set up fixtures for testing.
        case = self.create_standard_application_case(self.organisation)
        good = GoodFactory(
            organisation=self.organisation,
            is_good_controlled=True,
            control_list_entries=["ML21"],
        )
        FinalAdviceFactory(user=self.gov_user, team=self.team, case=case, good=good, type=AdviceType.APPROVE)
        GoodOnLicenceFactory(
            good=GoodOnApplicationFactory(application=case, good=good),
            licence=StandardLicenceFactory(case=case),
            quantity=100,
            value=1,
        )

    def test_good_on_licenses(self):
        url = reverse("data_workspace:v1:dw-good-on-licences-list")
        expected_fields = (
            "good_on_application_id",
            "usage",
            "name",
            "description",
            "units",
            "applied_for_quantity",
            "applied_for_value",
            "licenced_quantity",
            "licenced_value",
            "applied_for_value_per_item",
            "licenced_value_per_item",
            "is_good_controlled",
            "control_list_entries",
            "advice",
            "id",
            "licence_id",
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)

    def test_licenses(self):
        url = reverse("data_workspace:v1:dw-licences-list")
        expected_fields = ("id", "application", "reference_code", "status")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)
