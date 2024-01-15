import mohawk

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from urllib import parse

from api.core.requests import get_hawk_sender
from api.applications.tests.factories import GoodOnApplicationFactory
from api.cases.tests.factories import FinalAdviceFactory
from api.cases.enums import AdviceType
from api.goods.tests.factories import GoodFactory
from api.licences.tests.factories import StandardLicenceFactory, GoodOnLicenceFactory
from test_helpers.clients import DataTestClient


class DataWorkspaceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        test_host = "http://testserver"
        self.licences = parse.urljoin(test_host, reverse("data_workspace:dw-licences-only-list"))
        self.ogl_list = parse.urljoin(test_host, reverse("data_workspace:dw-ogl-only-list"))
        # Set up fixtures for testing.
        case = self.create_standard_application_case(self.organisation)
        good = GoodFactory(
            organisation=self.organisation,
            is_good_controlled=True,
            control_list_entries=["ML21"],
        )
        good_advice = FinalAdviceFactory(
            user=self.gov_user, team=self.team, case=case, good=good, type=AdviceType.APPROVE
        )
        GoodOnLicenceFactory(
            good=GoodOnApplicationFactory(application=case, good=good),
            licence=StandardLicenceFactory(case=case),
            quantity=100,
            value=1,
        )

    @override_settings(HAWK_AUTHENTICATION_ENABLED=True)
    def test_dw_view_licences(self):
        sender = get_hawk_sender("GET", self.licences, None, settings.HAWK_LITE_DATA_WORKSPACE_CREDENTIALS)
        self.client.credentials(HTTP_HAWK_AUTHENTICATION=sender.request_header, CONTENT_TYPE="application/json")
        response = self.client.get(self.licences)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(HAWK_AUTHENTICATION_ENABLED=True)
    def test_dw_view_licences_fail_incorrect_hawk_key(self):
        sender = get_hawk_sender("GET", self.licences, None, "internal-frontend")
        self.client.credentials(HTTP_HAWK_AUTHENTICATION=sender.request_header, CONTENT_TYPE="application/json")
        with self.assertRaises(mohawk.exc.HawkFail):
            self.client.get(self.licences)

    @override_settings(HAWK_AUTHENTICATION_ENABLED=True)
    def test_dw_view_ogl_types(self):
        sender = get_hawk_sender("GET", self.ogl_list, None, settings.HAWK_LITE_DATA_WORKSPACE_CREDENTIALS)
        self.client.credentials(HTTP_HAWK_AUTHENTICATION=sender.request_header, CONTENT_TYPE="application/json")
        response = self.client.get(self.ogl_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(HAWK_AUTHENTICATION_ENABLED=True)
    def test_dw_view_ogl_fail_incorrect_hawk_key(self):
        sender = get_hawk_sender("GET", self.ogl_list, None, "internal-frontend")
        self.client.credentials(HTTP_HAWK_AUTHENTICATION=sender.request_header, CONTENT_TYPE="application/json")
        with self.assertRaises(mohawk.exc.HawkFail):
            self.client.get(self.ogl_list)

    def test_good_on_licenses(self):
        url = reverse("data_workspace:dw-good-on-licences-list")
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
        url = reverse("data_workspace:dw-licences-list")
        expected_fields = ("id", "reference_code", "status", "application", "goods")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertGreater(len(results), 0)
        self.assertEqual(tuple(results[0].keys()), expected_fields)

        response = self.client.options(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["actions"]["OPTIONS"]
        self.assertEqual(tuple(options.keys()), expected_fields)
