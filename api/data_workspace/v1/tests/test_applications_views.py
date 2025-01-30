from django.urls import reverse
from rest_framework import status
from rest_framework.fields import DateTimeField

from urllib import parse

from api.applications.enums import ApplicationExportType, ApplicationExportLicenceOfficialType
from test_helpers.clients import DataTestClient
from api.applications.models import GoodOnApplication, GoodOnApplicationControlListEntry
from api.applications.tests.factories import StandardApplicationFactory
from api.organisations.tests.factories import OrganisationFactory
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

    def test_dw_standard_application_GET(self):
        organisation = OrganisationFactory(type="commercial")
        standard_application = StandardApplicationFactory(
            name="Test",
            export_type=ApplicationExportType.TEMPORARY,
            have_you_been_informed=ApplicationExportLicenceOfficialType.YES,
            reference_number_on_information_form="123",
            organisation=organisation,
        )

        drf_str_datetime = DateTimeField().to_representation
        response = self.client.get(self.standard_applications)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "count": 1,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": str(standard_application.pk),
                        "created_at": drf_str_datetime(standard_application.created_at),
                        "updated_at": drf_str_datetime(standard_application.updated_at),
                        "export_type": {"key": "temporary"},
                        "reference_code": standard_application.reference_code,
                        "submitted_at": None,
                        "name": "Test",
                        "activity": "Trade",
                        "is_eu_military": False,
                        "is_informed_wmd": False,
                        "is_suspected_wmd": False,
                        "is_compliant_limitations_eu": None,
                        "is_military_end_use_controls": False,
                        "intended_end_use": "this is our intended end use",
                        "agreed_to_foi": None,
                        "foi_reason": "",
                        "reference_number_on_information_form": "123",
                        "have_you_been_informed": "yes",
                        "is_shipped_waybill_or_lading": True,
                        "is_temp_direct_control": None,
                        "proposed_return_date": None,
                        "sla_days": 0,
                        "sla_remaining_days": None,
                        "sla_updated_at": None,
                        "last_closed_at": None,
                        "submitted_by": standard_application.submitted_by.baseuser_ptr.get_full_name(),
                        "status": {"id": "00000000-0000-0000-0000-000000000001"},
                        "case_type": {"id": "00000000-0000-0000-0000-000000000004"},
                        "organisation": {"id": str(standard_application.organisation.pk)},
                        "case_officer": None,
                        "copy_of": None,
                        "is_amended": False,
                        "destinations": {"data": ""},
                        "goods_starting_point": "GB",
                        "amendment_of": None,
                        "superseded_by": None,
                    }
                ],
            },
        )

    def test_dw_standard_application_GET_amendment_application(self):
        superseded_application = StandardApplicationFactory()
        amendment_application = StandardApplicationFactory(
            amendment_of=superseded_application,
        )

        drf_str_datetime = DateTimeField().to_representation
        response = self.client.get(self.standard_applications)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.json()["results"]

        superseded_application_response = results[0]
        self.assertEqual(superseded_application_response["id"], str(superseded_application.id))
        self.assertEqual(
            superseded_application_response["superseded_by"],
            str(amendment_application.id),
        )
        self.assertEqual(superseded_application_response["amendment_of"], None)

        amended_application_response = results[1]
        self.assertEqual(amended_application_response["id"], str(amendment_application.id))
        self.assertEqual(
            amended_application_response["amendment_of"],
            str(superseded_application.id),
        )
        self.assertEqual(amended_application_response["superseded_by"], None)

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
            "created_at",
            "updated_at",
            "quantity",
            "unit",
            "value",
            "is_good_incorporated",
            "application_id",
            "comment",
            "report_summary",
            "end_use_control",
            "is_precedent",
            "good",
            "firearm_details",
            "is_good_controlled",
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
            "created_at",
            "updated_at",
            "quantity",
            "unit",
            "value",
            "is_good_incorporated",
            "application_id",
            "comment",
            "report_summary",
            "end_use_control",
            "is_precedent",
            "good",
            "firearm_details",
            "is_good_controlled",
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
