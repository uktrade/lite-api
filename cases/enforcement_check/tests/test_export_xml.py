from uuid import UUID

from django.urls import reverse
from rest_framework import status
from xml.etree import ElementTree  # nosec

from applications.models import SiteOnApplication, ExternalLocationOnApplication
from cases.enforcement_check.export_xml import _get_address_line_2
from conf.constants import GovPermissions
from flags.enums import SystemFlags
from flags.models import Flag
from lite_content.lite_api.strings import Cases
from parties.enums import PartyType, PartyRole
from test_helpers.clients import DataTestClient


class ExportXML(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("cases:enforcement_check", kwargs={"queue_pk": self.queue.pk})

    @staticmethod
    def _xml_to_dict(stakeholder):
        return {
            "ELA_ID": stakeholder[0].text,
            "SH_ID": stakeholder[2].text,
            "SH_TYPE": stakeholder[3].text,
            "COUNTRY": stakeholder[4].text,
            "ORG_NAME": stakeholder[5].text,
            "PD_SURNAME": stakeholder[6].text,
            "ADDRESS1": stakeholder[9].text,
            "ADDRESS2": stakeholder[10].text,
        }

    def test_export_xml_with_parties_success(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, site=False)
        application.queues.set([self.queue])
        application.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)
        application_id_int = application.pk.int

        response = self.client.get(self.url, **self.gov_headers)
        application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = ElementTree.fromstring(response.content.decode("utf-8"))  # nosec
        # Does not include the organisation (last item)
        for stakeholder in data[:-1]:
            stakeholder = self._xml_to_dict(stakeholder)
            self.assertEqual(stakeholder["ELA_ID"], str(application_id_int))
            self.assertIsNotNone(stakeholder["SH_ID"])
            party = application.parties.get(party__id=UUID(int=int(stakeholder["SH_ID"]))).party
            self.assertIsNotNone(party)
            self.assertEqual(
                stakeholder["SH_TYPE"], party.type.upper() if party.type != PartyType.THIRD_PARTY else "OTHER"
            )
            self.assertEqual(stakeholder["COUNTRY"], party.country.name)
            self.assertEqual(stakeholder["ORG_NAME"], party.organisation.name)
            self.assertEqual(stakeholder["PD_SURNAME"], party.name)
            self.assertEqual(stakeholder["ADDRESS1"], party.address)

    def test_export_xml_with_contact_success(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, parties=False)
        application.queues.set([self.queue])
        application.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)
        self.create_party(
            "Contact", self.organisation, PartyType.THIRD_PARTY, application=application, role=PartyRole.CONTACT
        )

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = ElementTree.fromstring(response.content.decode("utf-8"))  # nosec
        stakeholder = self._xml_to_dict(data[0])

        self.assertEqual(stakeholder["ELA_ID"], str(application.pk.int))
        self.assertIsNotNone(stakeholder["SH_ID"])
        party = application.parties.get(party__id=UUID(int=int(stakeholder["SH_ID"]))).party
        self.assertIsNotNone(party)
        self.assertEqual(stakeholder["SH_TYPE"], "CONTACT")

    def test_export_xml_with_site_success(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, parties=False, site=False)
        application.queues.set([self.queue])
        application.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)
        site_on_application = SiteOnApplication.objects.create(
            site=self.organisation.primary_site, application=application
        )
        site = site_on_application.site

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = ElementTree.fromstring(response.content.decode("utf-8"))  # nosec
        stakeholder = self._xml_to_dict(data[0])

        self.assertEqual(stakeholder["ELA_ID"], str(application.pk.int))
        self.assertEqual(stakeholder["SH_ID"], str(site.pk.int))
        self.assertEqual(stakeholder["SH_TYPE"], "SOURCE")
        self.assertEqual(stakeholder["COUNTRY"], site.address.country.name)
        self.assertEqual(stakeholder["ORG_NAME"], site.organisation.name)
        self.assertEqual(stakeholder["ADDRESS1"], site.address.address_line_1)
        self.assertEqual(
            stakeholder["ADDRESS2"],
            _get_address_line_2(site.address.address_line_2, site.address.postcode, site.address.city),
        )

    def test_export_xml_with_external_location_success(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, parties=False, site=False)
        application.queues.set([self.queue])
        application.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)
        location = self.create_external_location("external", self.organisation)
        ExternalLocationOnApplication.objects.create(external_location=location, application=application)

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = ElementTree.fromstring(response.content.decode("utf-8"))  # nosec
        stakeholder = self._xml_to_dict(data[0])

        self.assertEqual(stakeholder["ELA_ID"], str(application.pk.int))
        self.assertEqual(stakeholder["SH_ID"], str(location.pk.int))
        self.assertEqual(stakeholder["SH_TYPE"], "SOURCE")
        self.assertEqual(stakeholder["COUNTRY"], location.country.name)
        self.assertEqual(stakeholder["ORG_NAME"], location.organisation.name)
        self.assertEqual(stakeholder["ADDRESS1"], location.address)

    def test_export_xml_organisation_only_success(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, parties=False, site=False)
        application.queues.set([self.queue])
        application.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = ElementTree.fromstring(response.content.decode("utf-8"))  # nosec
        stakeholder = self._xml_to_dict(data[0])

        self.assertEqual(stakeholder["ELA_ID"], str(application.pk.int))
        self.assertIsNotNone(stakeholder["SH_ID"], str(self.organisation.pk.int))
        self.assertEqual(stakeholder["SH_TYPE"], "LICENSEE")
        self.assertEqual(stakeholder["COUNTRY"], self.organisation.primary_site.address.country.name)
        self.assertEqual(stakeholder["ORG_NAME"], self.organisation.name)
        self.assertEqual(stakeholder["ADDRESS1"], self.organisation.primary_site.address.address_line_1)
        self.assertEqual(
            stakeholder["ADDRESS2"],
            _get_address_line_2(
                self.organisation.primary_site.address.address_line_2,
                self.organisation.primary_site.address.postcode,
                self.organisation.primary_site.address.city,
            ),
        )

    def test_export_xml_no_permission_failure(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_xml_no_cases_in_queue_failure(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation)
        application.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)
        queue = self.create_queue("Other", self.team)
        application.queues.set([queue])

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"][0], Cases.EnforcementCheck.NO_CASES)

    def test_export_xml_no_cases_with_flag_in_queue_failure(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation)
        application.queues.set([self.queue])

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errors"][0], Cases.EnforcementCheck.NO_CASES)
