import pytest
from dateutil.parser import parse
from parameterized import parameterized
from unittest.mock import patch

from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status

from django_elasticsearch_dsl_drf.filter_backends import SearchFilterBackend

from api.applications.tests.factories import GoodFactory, GoodOnApplicationFactory, StandardApplicationFactory
from api.cases.models import CaseReferenceCode
from api.goods.models import Good
from api.organisations.tests.factories import OrganisationFactory
from api.search.product.documents import ProductDocumentType
from api.search.product.views import ProductDocumentView

from api.teams.tests.factories import TeamFactory
from api.users.models import GovUser
from api.users.tests.factories import BaseUserFactory, GovUserFactory
from test_helpers.clients import DataTestClient


def get_users_data():
    return [
        {
            "first_name": "TAU",
            "last_name": "Advisor1",
        },
        {
            "first_name": "TAU",
            "last_name": "Advisor2",
        },
        {
            "first_name": "TAU",
            "last_name": "Advisor3",
        },
    ]


def get_products_data(organisation, application, gov_users):
    return [
        {
            "good": {
                "name": "Bolt action sporting rifle",
                "part_number": "ABC-123",
                "organisation": organisation,
                "is_good_controlled": True,
                "control_list_entries": ["FR AI"],
            },
            "good_on_application": {
                "application": application,
                "is_good_controlled": True,
                "report_summary": "sniper rifles",
                "assessed_by": gov_users[0],
                "assessment_date": parse("2021-06-08T15:51:28.529110+00:00"),
                "comment": "no concerns",
            },
        },
        {
            "good": {
                "name": "Thermal camera",
                "part_number": "IMG-1300",
                "organisation": organisation,
                "is_good_controlled": True,
                "control_list_entries": ["6A003"],
            },
            "good_on_application": {
                "application": application,
                "is_good_controlled": True,
                "report_summary": "Imaging sensors",
                "assessed_by": gov_users[0],
                "assessment_date": parse("2021-07-08T15:51:28.529110+00:00"),
                "comment": "for industrial use only",
            },
        },
        {
            "good": {
                "name": "Magnetic field sensor",
                "part_number": "TS1.5/M2",
                "organisation": organisation,
                "is_good_controlled": True,
                "control_list_entries": ["6A006"],
            },
            "good_on_application": {
                "application": application,
                "is_good_controlled": True,
                "report_summary": "Magnetic sensors",
                "assessed_by": gov_users[0],
                "assessment_date": parse("2022-08-20T15:51:28.529110+00:00"),
                "comment": "for industrial use only",
            },
        },
        {
            "good": {
                "name": "Frequency shifter",
                "part_number": "MS2X",
                "organisation": organisation,
                "is_good_controlled": True,
                "control_list_entries": ["6A004"],
            },
            "good_on_application": {
                "application": application,
                "is_good_controlled": True,
                "report_summary": "components for spectrometers",
                "comment": "Research and development. Potentially under WVS regime",
            },
        },
        {
            "good": {
                "name": "Cherry MX Red",
                "part_number": "MXR125H",
                "organisation": organisation,
                "is_good_controlled": True,
                "control_list_entries": ["PL9010"],
            },
            "good_on_application": {
                "application": application,
                "is_good_controlled": True,
                "report_summary": "mechanical keyboards",
                "assessed_by": gov_users[1],
                "assessment_date": parse("2022-10-08T15:51:28.529110+00:00"),
                "comment": "dual use",
            },
        },
        {
            "good": {
                "name": "Sulphuric Acid",
                "part_number": "H2SO4",
                "organisation": organisation,
                "is_good_controlled": True,
                "control_list_entries": ["1D003"],
            },
            "good_on_application": {
                "application": application,
                "is_good_controlled": True,
                "report_summary": "Chemicals",
                "assessed_by": gov_users[1],
                "assessment_date": parse("2023-10-21T15:51:28.529110+00:00"),
                "comment": "industrial use",
            },
        },
        {
            "good": {
                "name": "M3 Pro Max",
                "part_number": "867-5309",
                "organisation": organisation,
                "is_good_controlled": True,
                "control_list_entries": ["6A001a1d"],
            },
            "good_on_application": {
                "application": application,
                "is_good_controlled": True,
                "report_summary": "marine position fixing equipment",
                "regime_entries": ["Wassenaar Arrangement"],
                "assessed_by": gov_users[2],
                "assessment_date": parse("2023-10-22T15:51:28.529110+00:00"),
            },
        },
        {
            "good": {
                "name": "Instax HD camera",
                "part_number": "abc123xyz",
                "organisation": organisation,
                "is_good_controlled": True,
                "control_list_entries": ["6A003b4a"],
            },
            "good_on_application": {
                "application": application,
                "is_good_controlled": True,
                "report_summary": "components for imaging cameras",
                "regime_entries": ["Wassenaar Arrangement Sensitive"],
                "assessed_by": gov_users[2],
                "assessment_date": parse("2023-10-23T15:51:28.529110+00:00"),
            },
        },
        {
            "good": {
                "name": "controlled chemical substance",
                "part_number": "H2O2",
                "organisation": organisation,
                "is_good_controlled": True,
                "control_list_entries": ["1C35016"],
            },
            "good_on_application": {
                "application": application,
                "is_good_controlled": True,
                "report_summary": "chemicals used for general laboratory work/scientific research",
                "regime_entries": ["CWC Schedule 3"],
                "assessed_by": gov_users[2],
                "assessment_date": parse("2023-10-24T15:51:28.529110+00:00"),
            },
        },
        {
            "good": {
                "name": "Maintenance manual",
                "part_number": "15606",
                "organisation": organisation,
                "is_good_controlled": False,
                "control_list_entries": ["ML22a"],
            },
            "good_on_application": {
                "application": application,
                "is_good_controlled": False,
                "report_summary": "technology for shotguns",
                "assessment_date": parse("2023-08-24T15:51:28.529110+00:00"),
            },
        },
    ]


class ProductSearchTests(DataTestClient):
    product_search_url = reverse("product_search-list")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.organisation = OrganisationFactory(name="Product search")
        cls.application = StandardApplicationFactory()

        cls.team = TeamFactory()
        cls.tau_users = [
            GovUserFactory(baseuser_ptr=BaseUserFactory(**user), team=cls.team) for user in get_users_data()
        ]

        # Create few products and add them to an application
        for product in get_products_data(cls.organisation, cls.application, cls.tau_users):
            GoodOnApplicationFactory(good=GoodFactory(**product["good"]), **product["good_on_application"])

        # Rebuild indexes with the products created
        call_command("search_index", models=["applications.GoodOnApplication"], action="rebuild", force=True)

    @classmethod
    def tearDownClass(cls):
        # Clean up all the objects created for these tests
        # Some other tests expecting certain reference codes and count of goods
        # so they will fail if these are not cleanedup properly.
        Good.objects.filter(organisation=cls.organisation).delete()
        GovUser.objects.filter(team=cls.team).delete()
        cls.application.delete()
        CaseReferenceCode.objects.all().delete()
        cls.team.delete()

    def test_search_results_serializer(self):
        document = ProductDocumentType()
        expected_fields = list(document._fields.keys())
        # remove fields not exposed to UI
        for key in ("wildcard", "context", "end_user_type"):
            if key in expected_fields:
                expected_fields.remove(key)

        request = RequestFactory().get(self.product_search_url)
        view = ProductDocumentView()
        view.request = request
        view.format_kwarg = None
        queryset = view.get_queryset()
        view.augment_hits_with_instances(queryset)
        serializer = view.get_serializer(queryset, many=True)
        actual_fields = serializer.data[0].keys()

        self.assertTrue(set(expected_fields).issubset(set(actual_fields)))

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
                {"search": "rifle"},
                1,
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
            ({"search": "H2SO4"}, 1, "H2SO4"),
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
            ({"search": "Advisor2"}, 2),
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
        expected_count = Good.objects.filter(organisation=self.organisation).count()
        response = self.client.get(self.product_search_url, query_params, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        response = response.json()
        self.assertEqual(response["count"], expected_count)

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

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "rifle"}, 1),
            ({"search": "shifter AND 6A004"}, 1),
            ({"search": "sensor AND 6A006"}, 1),
            ({"search": "sensor AND 6A*"}, 2),
            ({"search": "sensor AND (thermal OR magnetic)"}, 2),
            ({"search": "Wassenaar AND 6A001a1d"}, 1),
            ({"search": "Wassenaar AND 6a001a1d"}, 1),
            ({"search": "Chemicals AND (WS OR CWC)"}, 1),
            ({"search": '"Thermal camera"'}, 1),
            ({"search": "components NOT camera"}, 1),
        ]
    )
    def test_product_search_query_string_queries(self, query, expected_count):
        response = self.client.get(self.product_search_url, query, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        response = response.json()
        self.assertEqual(response["count"], expected_count)

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "sensor AND"}, 0),
            ({"search": "sensor OR"}, 0),
            ({"search": "sensor AND (image NOT)"}, 0),
            ({"search": "AND sensor"}, 0),
        ]
    )
    def test_product_search_syntax_error(self, query, expected_count):
        response = self.client.get(self.product_search_url, query, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = response.json()
        self.assertEqual(response["error"], "Invalid search string")
        self.assertEqual(response["count"], expected_count)

    @pytest.mark.elasticsearch
    @parameterized.expand(
        [
            ({"search": "sensor AND"},),
            ({"search": "sensor OR"},),
            ({"search": "sensor AND (image NOT)"},),
            ({"search": "AND sensor"},),
        ]
    )
    @patch("api.search.product.views.ProductDocumentView", spec=True)
    def test_product_search_no_syntax_error_without_query_string_backend(self, query, mock_view):
        """
        We only need to check for syntax errors if we are using QueryString backend.
        If we are not using then these queries should not fail
        """
        current_filter_backends = getattr(mock_view.__class__, "filter_backends")
        setattr(mock_view.__class__, "filter_backends", [SearchFilterBackend])

        response = self.client.get(self.product_search_url, query, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        # Attributes are bound to class, as we have updated above we need
        # to restore after the test.
        setattr(mock_view.__class__, "filter_backends", current_filter_backends)


class MoreLikeThisViewTests(DataTestClient):
    @pytest.mark.elasticsearch
    def test_more_like_this_404(self):
        url = reverse("more_like_this", kwargs={"pk": "a1e4d94f-8519-4ef3-8863-e8fa17bdd685"})

        response = self.client.get(url, **self.gov_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
