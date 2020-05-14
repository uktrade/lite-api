from uuid import UUID

from django.urls import reverse
from rest_framework import status
from xml.etree import ElementTree  # nosec

from applications.models import SiteOnApplication
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
        self.enforcement_check_flag = Flag.objects.get(id=SystemFlags.ENFORCEMENT_CHECK_REQUIRED)

    def test_export_xml_with_parties_success(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, site=False)
        application.queues.set([self.queue])
        application.flags.add(self.enforcement_check_flag)
        application_id_int = application.pk.int

        response = self.client.get(self.url, **self.gov_headers)
        application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = ElementTree.fromstring(response.content.decode("utf-8"))  # nosec
        # Does not include the organisation (last item)
        for stakeholder in data[:-1]:
            # ELA_ID
            self.assertEqual(stakeholder[0].text, str(application_id_int))
            # SH_ID
            self.assertIsNotNone(stakeholder[2].text)
            party = application.parties.get(party__id=UUID(int=int(stakeholder[2].text))).party
            self.assertIsNotNone(party)
            # SH_TYPE
            self.assertEqual(
                stakeholder[3].text, party.type.upper() if party.type != PartyType.THIRD_PARTY else "OTHER"
            )
            # COUNTRY
            self.assertEqual(stakeholder[4].text, party.country.name)
            # ORG_NAME
            self.assertEqual(stakeholder[5].text, party.organisation.name)
            # PD_SURNAME
            self.assertEqual(stakeholder[6].text, party.name)
            # ADDRESS1
            self.assertEqual(stakeholder[9].text, party.address)

    def test_export_xml_with_contact_success(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, parties=False)
        application.queues.set([self.queue])
        application.flags.add(self.enforcement_check_flag)
        self.create_party(
            "Contact", self.organisation, PartyType.THIRD_PARTY, application=application, role=PartyRole.CONTACT
        )

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = ElementTree.fromstring(response.content.decode("utf-8"))  # nosec
        stakeholder = data[0]

        self.assertEqual(stakeholder[0].text, str(application.pk.int))
        # SH_ID
        self.assertIsNotNone(stakeholder[2].text)
        party = application.parties.get(party__id=UUID(int=int(stakeholder[2].text))).party
        self.assertIsNotNone(party)
        # SH_TYPE
        self.assertEqual(stakeholder[3].text, "CONTACT")

    def test_export_xml_with_site_success(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, parties=False, site=False)
        application.queues.set([self.queue])
        application.flags.add(self.enforcement_check_flag)
        site_on_application = SiteOnApplication.objects.create(
            site=self.organisation.primary_site, application=application
        )
        site = site_on_application.site

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = ElementTree.fromstring(response.content.decode("utf-8"))  # nosec
        stakeholder = data[0]

        self.assertEqual(stakeholder[0].text, str(application.pk.int))
        # SH_ID
        self.assertIsNotNone(stakeholder[2].text, str(site.pk.int))
        # SH_TYPE
        self.assertEqual(stakeholder[3].text, "SOURCE")
        # COUNTRY
        self.assertEqual(stakeholder[4].text, site.address.country.name)
        # ORG_NAME
        self.assertEqual(stakeholder[5].text, site.organisation.name)
        # ADDRESS1
        self.assertEqual(stakeholder[9].text, site.address.address_line_1)
        # ADDRESS2
        self.assertEqual(stakeholder[10].text, site.address.address_line_2)

    def test_export_xml_organisation_only_success(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, parties=False, site=False)
        application.queues.set([self.queue])
        application.flags.add(self.enforcement_check_flag)

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = ElementTree.fromstring(response.content.decode("utf-8"))  # nosec
        stakeholder = data[0]

        self.assertEqual(stakeholder[0].text, str(application.pk.int))
        # SH_ID
        self.assertIsNotNone(stakeholder[2].text, str(self.organisation.pk.int))
        # SH_TYPE
        self.assertEqual(stakeholder[3].text, "LICENSEE")
        # COUNTRY
        self.assertEqual(stakeholder[4].text, self.organisation.primary_site.address.country.name)
        # ORG_NAME
        self.assertEqual(stakeholder[5].text, self.organisation.name)
        # ADDRESS1
        self.assertEqual(stakeholder[9].text, self.organisation.primary_site.address.address_line_1)
        # ADDRESS2
        self.assertEqual(stakeholder[10].text, self.organisation.primary_site.address.address_line_2)

    def test_export_xml_no_permission_failure(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_xml_no_cases_in_queue_failure(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation)
        application.flags.add(self.enforcement_check_flag)
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
