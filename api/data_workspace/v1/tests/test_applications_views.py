from django.urls import reverse
from rest_framework import status
from urllib import parse

from api.applications.enums import ApplicationExportType, ApplicationExportLicenceOfficialType
from test_helpers.clients import DataTestClient
from api.applications.models import GoodOnApplication, GoodOnApplicationControlListEntry
from api.cases.enums import CaseTypeReferenceEnum
from api.flags.enums import FlagLevels
from api.flags.tests.factories import FlagFactory
from api.goods.tests.factories import GoodFactory
from api.staticdata.units.enums import Units
from api.staticdata.control_list_entries.models import ControlListEntry


class DataWorkspaceApplicationViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        test_host = "http://testserver"
        self.standard_applications = parse.urljoin(
            test_host, reverse("data_workspace:v1:dw-standard-applications-list")
        )
        self.good_on_applications = parse.urljoin(test_host, reverse("data_workspace:v1:dw-good-on-applications-list"))
        self.good_on_applications_clc_entries = parse.urljoin(
            test_host, reverse("data_workspace:v1:dw-good-on-applications-control-list-entries-list")
        )
        self.party_on_applications = parse.urljoin(
            test_host, reverse("data_workspace:v1:dw-party-on-applications-list")
        )
        self.denial_on_applications = parse.urljoin(
            test_host, reverse("data_workspace:v1:dw-denial-match-on-applications-list")
        )

    def test_dw_standard_application_views(self):
        data = {
            "name": "Test",
            "application_type": CaseTypeReferenceEnum.SIEL,
            "export_type": ApplicationExportType.TEMPORARY,
            "have_you_been_informed": ApplicationExportLicenceOfficialType.YES,
            "reference_number_on_information_form": "123",
        }

        response = self.client.post(reverse("applications:applications"), data, **self.exporter_headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.options(self.standard_applications)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_keys = response.json()["actions"]["GET"].keys()
        expected_keys = (
            "id",
            "name",
            "organisation",
            "case_type",
            "export_type",
            "created_at",
            "updated_at",
            "submitted_at",
            "submitted_by",
            "status",
            "case",
            "reference_code",
            "case_officer",
            "agreed_to_foi",
            "foi_reason",
            "end_user",
            "consignee",
            "goods",
            "have_you_been_informed",
            "activity",
            "destinations",
            "denial_matches",
            "licence",
            "is_amended",
        )
        for key in expected_keys:
            self.assertTrue(key in actual_keys)

    def test_dw_good_on_application_views_OPTIONS(self):
        self.good = GoodFactory(
            organisation=self.organisation, flags=[FlagFactory(level=FlagLevels.GOOD, team=self.team)]
        )
        self.application = self.create_draft_standard_application(organisation=self.organisation)
        self.good_on_application = GoodOnApplication.objects.create(
            good=self.good, application=self.application, quantity=10, unit=Units.NAR, value=500
        )
        response = self.client.options(self.good_on_applications)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_keys = response.json()["actions"]["GET"].keys()
        expected_keys = [
            "id",
            "good",
            "application",
            "quantity",
            "unit",
            "value",
            "is_good_incorporated",
            "flags",
            "is_good_controlled",
            "control_list_entries",
            "report_summary",
            "firearm_details",
            "good_application_documents",
            "good_application_internal_documents",
            "is_precedent",
            "nsg_list_type",
            "is_trigger_list_guidelines_applicable",
            "is_nca_applicable",
            "nsg_assessment_note",
        ]
        for key in expected_keys:
            self.assertTrue(key in actual_keys)

        response = self.client.options(self.party_on_applications)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_keys = response.json()["actions"]["GET"].keys()
        expected_keys = ("id", "created_at", "updated_at", "deleted_at", "application", "party", "flags")
        self.assertEqual(tuple(actual_keys), expected_keys)

    def test_dw_good_on_application_views_GET(self):
        self.good = GoodFactory(
            organisation=self.organisation, flags=[FlagFactory(level=FlagLevels.GOOD, team=self.team)]
        )
        self.application = self.create_draft_standard_application(organisation=self.organisation)
        self.good_on_application = GoodOnApplication.objects.create(
            good=self.good, application=self.application, quantity=10, unit=Units.NAR, value=500
        )
        response = self.client.get(self.good_on_applications)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_keys = response.json()["results"][0].keys()
        expected_keys = [
            "id",
            "good",
            "application",
            "quantity",
            "unit",
            "value",
            "is_good_incorporated",
            "flags",
            "is_good_controlled",
            "control_list_entries",
            "report_summary",
            "firearm_details",
            "good_application_documents",
            "good_application_internal_documents",
            "is_precedent",
            "nsg_list_type",
            "is_trigger_list_guidelines_applicable",
            "is_nca_applicable",
            "nsg_assessment_note",
        ]
        for key in expected_keys:
            self.assertTrue(key in actual_keys)

        response = self.client.get(self.party_on_applications)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_keys = response.json()["results"][0].keys()
        expected_keys = ("id", "created_at", "updated_at", "deleted_at", "application", "party", "flags")
        self.assertEqual(tuple(actual_keys), expected_keys)

    def test_dw_good_on_application_control_list_entry_views(self):
        self.good = GoodFactory(
            organisation=self.organisation, flags=[FlagFactory(level=FlagLevels.GOOD, team=self.team)]
        )
        self.application = self.create_draft_standard_application(organisation=self.organisation)
        self.good_on_application = GoodOnApplication.objects.create(
            good=self.good, application=self.application, quantity=10, unit=Units.NAR, value=500
        )
        clc_entry = ControlListEntry.objects.first()
        GoodOnApplicationControlListEntry.objects.create(
            goodonapplication=self.good_on_application, controllistentry=clc_entry
        )
        response = self.client.options(self.good_on_applications_clc_entries)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_keys = response.json()["actions"]["GET"].keys()
        expected_keys = ("id", "goodonapplication", "controllistentry")
        self.assertEqual(tuple(actual_keys), expected_keys)

    def test_dw_denial_on_application_views(self):
        response = self.client.options(self.denial_on_applications)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual_keys = response.json()["actions"]["GET"].keys()
        expected_keys = {"id", "denial_entity", "application", "category"}
        self.assertEqual(expected_keys, actual_keys)
