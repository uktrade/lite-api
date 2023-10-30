import pytest

from dateutil.parser import parse
from parameterized import parameterized

from django.core.management import call_command
from django.urls import reverse

from api.applications.tests.factories import GoodFactory, GoodOnApplicationFactory
from api.teams.tests.factories import TeamFactory
from api.users.tests.factories import BaseUserFactory, GovUserFactory
from test_helpers.clients import DataTestClient


class ProductSearchTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.product_search_url = reverse("product_search-list")

        self.team = TeamFactory()
        self.tau_user1 = GovUserFactory(
            baseuser_ptr=BaseUserFactory(first_name="TAU", last_name="Advisor1"), team=self.team
        )
        self.tau_user2 = GovUserFactory(
            baseuser_ptr=BaseUserFactory(first_name="TAU", last_name="Advisor2"), team=self.team
        )

        # Create few products and add them to an application
        good = GoodFactory(
            name="Bolt action sporting rifle",
            part_number="ABC-123",
            organisation=self.organisation,
            is_good_controlled=True,
            control_list_entries=["FR AI"],
        )
        GoodOnApplicationFactory(
            application=self.case,
            good=good,
            is_good_controlled=True,
            report_summary="sniper rifles",
            assessed_by=self.tau_user1,
            assessment_date=parse("2021-06-08T15:51:28.529110+00:00"),
            comment="no concerns",
        )

        good = GoodFactory(
            name="Thermal camera",
            part_number="IMG-1300",
            organisation=self.organisation,
            is_good_controlled=True,
            control_list_entries=["6A003"],
        )
        GoodOnApplicationFactory(
            application=self.case,
            good=good,
            is_good_controlled=True,
            report_summary="Imaging sensors",
            assessed_by=self.tau_user1,
            assessment_date=parse("2021-07-08T15:51:28.529110+00:00"),
            comment="for industrial use only",
        )

        good = GoodFactory(
            name="Magnetic field sensor",
            part_number="TS1.5/M2",
            organisation=self.organisation,
            is_good_controlled=True,
            control_list_entries=["6A006"],
        )
        GoodOnApplicationFactory(
            application=self.case,
            good=good,
            is_good_controlled=True,
            report_summary="Magnetic sensors",
            assessed_by=self.tau_user1,
            assessment_date=parse("2022-08-20T15:51:28.529110+00:00"),
            comment="for industrial use only",
        )

        good = GoodFactory(
            name="Cherry MX Red",
            part_number="MXR125H",
            organisation=self.organisation,
            is_good_controlled=True,
            control_list_entries=["PL9010"],
        )
        GoodOnApplicationFactory(
            application=self.case,
            good=good,
            is_good_controlled=True,
            report_summary="mechanical keyboards",
            assessed_by=self.tau_user2,
            assessment_date=parse("2022-10-08T15:51:28.529110+00:00"),
            comment="dual use",
        )

        good = GoodFactory(
            name="Hydrofluoric Acid",
            part_number="HFL",
            organisation=self.organisation,
            is_good_controlled=True,
            control_list_entries=["1D003"],
        )
        GoodOnApplicationFactory(
            application=self.case,
            good=good,
            is_good_controlled=True,
            report_summary="Chemicals",
            assessed_by=self.tau_user2,
            assessment_date=parse("2023-10-21T15:51:28.529110+00:00"),
            comment="industrial use",
        )

        good = GoodFactory(
            name="M2 Pro Max",
            part_number="867-5309",
            organisation=self.organisation,
            is_good_controlled=True,
            control_list_entries=["6A001a1d"],
        )
        GoodOnApplicationFactory(
            application=self.case,
            good=good,
            is_good_controlled=True,
            report_summary="marine position fixing equipment",
            regime_entries=["Wassenaar Arrangement"],
            assessed_by=self.tau_user2,
            assessment_date=parse("2023-10-22T15:51:28.529110+00:00"),
        )

        good = GoodFactory(
            name="Instax HD camera",
            part_number="abc123xyz",
            organisation=self.organisation,
            is_good_controlled=True,
            control_list_entries=["6A003b4a"],
        )
        GoodOnApplicationFactory(
            application=self.case,
            good=good,
            is_good_controlled=True,
            report_summary="imaging cameras",
            regime_entries=["Wassenaar Arrangement Sensitive"],
            assessed_by=self.tau_user2,
            assessment_date=parse("2023-10-23T15:51:28.529110+00:00"),
        )

        good = GoodFactory(
            name="mom's homemade lemonade",
            part_number="xyz123",
            organisation=self.organisation,
            is_good_controlled=True,
            control_list_entries=["1C35016"],
        )
        GoodOnApplicationFactory(
            application=self.case,
            good=good,
            is_good_controlled=True,
            report_summary="chemicals used for general laboratory work/scientific research",
            regime_entries=["CWC Schedule 3"],
            assessed_by=self.tau_user2,
            assessment_date=parse("2023-10-24T15:51:28.529110+00:00"),
        )

        call_command("search_index", models=["applications.GoodOnApplication"], action="rebuild", force=True)

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "sporting"}, 1, "Bolt action sporting rifle"),
            (
                # note that we are providing search term in lowercase
                {"search": "bolt"},
                1,
                "Bolt action sporting rifle",
            ),
            (
                # one product is created during test setup stage which matches with this query
                {"search": "rifle"},
                2,
                "Bolt action sporting rifle",
            ),
            ({"search": "thermal"}, 1, "Thermal camera"),
        ]
    )
    def test_product_search_by_name(self, query, expected_count, expected_name):
        response = self.client.get(self.product_search_url, query, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        response = response.json()
        self.assertEqual(response["count"], expected_count)
        self.assertIn(expected_name, [item["name"] for item in response["results"]])

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "ABC"}, 1, "ABC-123"),
            ({"search": "HFL"}, 1, "HFL"),
        ]
    )
    def test_product_search_by_part_number(self, query, expected_count, expected_part_number):
        response = self.client.get(self.product_search_url, query, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        response = response.json()
        self.assertEqual(response["count"], expected_count)
        self.assertIn(expected_part_number, [item["part_number"] for item in response["results"]])

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "PL9010"}, 1, "PL9010"),
            ({"search": "6A003"}, 1, "6A003"),
            ({"search": "6A006"}, 1, "6A006"),
        ]
    )
    def test_product_search_by_control_list_entries(self, query, expected_count, expected_cle):
        response = self.client.get(self.product_search_url, query, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        response = response.json()
        self.assertEqual(response["count"], expected_count)
        self.assertIn(
            expected_cle, [entry["rating"] for item in response["results"] for entry in item["control_list_entries"]]
        )

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "Wassenaar Arrangement"}, 2, "W", "Wassenaar Arrangement"),
            ({"search": "WS"}, 1, "WS", "Wassenaar Arrangement Sensitive"),
            ({"search": "CWC 3"}, 1, "CWC 3", "CWC Schedule 3"),
        ]
    )
    def test_product_search_by_regime(
        self, query, expected_count, expected_regime_shortened_name, expected_regime_name
    ):
        response = self.client.get(self.product_search_url, query, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        response = response.json()
        self.assertEqual(response["count"], expected_count)
        self.assertIn(
            expected_regime_shortened_name,
            [entry["shortened_name"] for item in response["results"] for entry in item["regime_entries"]],
        )
        self.assertIn(
            expected_regime_name,
            [entry["name"] for item in response["results"] for entry in item["regime_entries"]],
        )

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "sensor"}, 2, "Magnetic sensors"),
            ({"search": "sensor"}, 2, "Imaging sensors"),
            ({"search": "chemicals"}, 2, "Chemicals"),
        ]
    )
    def test_product_search_by_report_summary(self, query, expected_count, expected_report_summary):
        response = self.client.get(self.product_search_url, query, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        response = response.json()
        self.assertEqual(response["count"], expected_count)
        self.assertIn(expected_report_summary, [item["report_summary"] for item in response["results"]])

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "Advisor1"}, 3),
            ({"search": "Advisor2"}, 5),
        ]
    )
    def test_product_search_by_assessing_officer(self, query, expected_count):
        response = self.client.get(self.product_search_url, query, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        response = response.json()
        self.assertEqual(response["count"], expected_count)

    @pytest.mark.elasticsearch
    def test_product_search_by_applicant(self):
        query_params = {"search": f"{self.organisation.name}"}
        response = self.client.get(self.product_search_url, query_params, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        response = response.json()
        self.assertEqual(response["count"], 6)

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "industrial"}, 3),
            ({"search": "dual"}, 1),
        ]
    )
    def test_product_search_by_assessment_note(self, query, expected_count):
        response = self.client.get(self.product_search_url, query, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        response = response.json()
        self.assertEqual(response["count"], expected_count)


class MoreLikeThisViewTests(DataTestClient):
    @pytest.mark.elasticsearch
    def test_more_like_this_404(self):
        url = reverse("more_like_this", kwargs={"pk": "a1e4d94f-8519-4ef3-8863-e8fa17bdd685"})

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
