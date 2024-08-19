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
                        "activity": "Trade",
                        "additional_documents": [],
                        "agreed_to_foi": None,
                        "amendment_of": None,
                        "appeal": None,
                        "appeal_deadline": None,
                        "case": str(standard_application.id),
                        "case_officer": None,
                        "case_type": {
                            "id": "00000000-0000-0000-0000-000000000004",
                            "reference": {"key": "siel", "value": "Standard Individual Export " "Licence"},
                            "sub_type": {"key": "standard", "value": "Standard Licence"},
                            "type": {"key": "application", "value": "Application"},
                        },
                        "compliant_limitations_eu_ref": None,
                        "consignee": None,
                        "created_at": drf_str_datetime(standard_application.created_at),
                        "denial_matches": [],
                        "destinations": {"data": "", "type": "end_user"},
                        "end_user": None,
                        "export_type": {"key": "temporary", "value": "Temporary"},
                        "f1686_approval_date": None,
                        "f1686_contracting_authority": None,
                        "f1686_reference_number": None,
                        "f680_reference_number": None,
                        "foi_reason": "",
                        "goods": [],
                        "goods_locations": {},
                        "goods_recipients": "direct_to_end_user",
                        "goods_starting_point": "GB",
                        "have_you_been_informed": "yes",
                        "id": str(standard_application.id),
                        "inactive_parties": [],
                        "informed_wmd_ref": None,
                        "intended_end_use": "this is our intended end use",
                        "is_amended": False,
                        "is_compliant_limitations_eu": None,
                        "is_eu_military": False,
                        "is_informed_wmd": False,
                        "is_major_editable": False,
                        "is_military_end_use_controls": False,
                        "is_mod_security_approved": False,
                        "is_shipped_waybill_or_lading": True,
                        "is_suspected_wmd": False,
                        "is_temp_direct_control": None,
                        "last_closed_at": None,
                        "licence": None,
                        "military_end_use_controls_ref": None,
                        "name": "Test",
                        "non_waybill_or_lading_route_details": None,
                        "organisation": {
                            "created_at": drf_str_datetime(organisation.created_at),
                            "documents": [],
                            "eori_number": organisation.eori_number,
                            "flags": None,
                            "id": str(organisation.id),
                            "name": organisation.name,
                            "phone_number": "",
                            "primary_site": {
                                "address": {
                                    "address_line_1": organisation.primary_site.address.address_line_1,
                                    "address_line_2": organisation.primary_site.address.address_line_2,
                                    "city": organisation.primary_site.address.city,
                                    "country": {
                                        "id": organisation.primary_site.address.country.id,
                                        "is_eu": organisation.primary_site.address.country.is_eu,
                                        "name": organisation.primary_site.address.country.name,
                                        "report_name": organisation.primary_site.address.country.report_name,
                                        "type": organisation.primary_site.address.country.type,
                                    },
                                    "id": str(organisation.primary_site.address.id),
                                    "postcode": organisation.primary_site.address.postcode,
                                    "region": organisation.primary_site.address.region,
                                },
                                "id": str(organisation.primary_site.id),
                                "name": organisation.primary_site.name,
                                "records_located_at": {
                                    "address": {
                                        "address_line_1": organisation.primary_site.site_records_located_at.address.address_line_1,
                                        "address_line_2": organisation.primary_site.site_records_located_at.address.address_line_2,
                                        "city": organisation.primary_site.site_records_located_at.address.city,
                                        "country": {
                                            "name": organisation.primary_site.site_records_located_at.address.country.name,
                                        },
                                        "postcode": organisation.primary_site.site_records_located_at.address.postcode,
                                        "region": organisation.primary_site.site_records_located_at.address.region,
                                    },
                                    "id": str(organisation.primary_site.site_records_located_at.id),
                                    "name": organisation.primary_site.site_records_located_at.name,
                                },
                            },
                            "registration_number": organisation.registration_number,
                            "sic_number": organisation.sic_number,
                            "status": {"key": "active", "value": "Active"},
                            "type": {"key": "commercial", "value": "Commercial Organisation"},
                            "updated_at": drf_str_datetime(organisation.updated_at),
                            "vat_number": organisation.vat_number,
                            "website": "",
                        },
                        "other_security_approval_details": None,
                        "proposed_return_date": None,
                        "reference_code": standard_application.reference_code,
                        "reference_number_on_information_form": "123",
                        "sanction_matches": [],
                        "security_approvals": None,
                        "sla_days": 0,
                        "sla_remaining_days": None,
                        "sla_updated_at": None,
                        "status": {
                            "id": "00000000-0000-0000-0000-000000000001",
                            "key": "submitted",
                            "value": "Submitted",
                        },
                        "sub_status": None,
                        "subject_to_itar_controls": None,
                        "submitted_at": None,
                        "submitted_by": standard_application.submitted_by.baseuser_ptr.get_full_name(),
                        "superseded_by": None,
                        "suspected_wmd_ref": None,
                        "temp_direct_control_details": None,
                        "temp_export_details": None,
                        "third_parties": [],
                        "trade_control_activity": {"key": None, "value": None},
                        "trade_control_product_categories": [],
                        "ultimate_end_users": [],
                        "updated_at": drf_str_datetime(standard_application.updated_at),
                        "usage": "Trade",
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
