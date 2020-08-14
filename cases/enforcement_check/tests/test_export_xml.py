from xml.etree import ElementTree  # nosec

from django.urls import reverse
from rest_framework import status

from api.applications.models import SiteOnApplication, ExternalLocationOnApplication
from cases.enforcement_check.export_xml import _get_address_line_2, get_enforcement_id
from cases.enforcement_check.import_xml import enforcement_id_to_uuid
from cases.enums import EnforcementXMLEntityTypes
from cases.models import EnforcementCheckID
from api.conf.constants import GovPermissions
from api.flags.enums import SystemFlags
from api.parties.enums import PartyType, PartyRole
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

    def _assert_enforcement_type_recorded(self, stakholder_id, entity_uuid, type):
        self.assertTrue(
            EnforcementCheckID.objects.filter(id=stakholder_id, entity_id=entity_uuid, entity_type=type).exists()
        )

    def test_export_xml_with_parties_success(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, site=False)
        application.queues.set([self.queue])
        application.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)

        response = self.client.get(self.url, **self.gov_headers)
        application.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = ElementTree.fromstring(response.content.decode("utf-8"))  # nosec
        application_id_int = str(get_enforcement_id(application.pk))
        # Does not include the organisation (last item)
        for stakeholder in data[:-1]:
            stakeholder = self._xml_to_dict(stakeholder)
            self.assertEqual(stakeholder["ELA_ID"], application_id_int)
            self.assertIsNotNone(stakeholder["SH_ID"])
            entity_uuid = enforcement_id_to_uuid(stakeholder["SH_ID"])
            party = application.parties.get(party__id=entity_uuid).party
            self.assertIsNotNone(party)
            self.assertEqual(
                stakeholder["SH_TYPE"], party.type.upper() if party.type != PartyType.THIRD_PARTY else "OTHER"
            )
            self.assertEqual(stakeholder["COUNTRY"], party.country.name)
            self.assertEqual(stakeholder["ORG_NAME"], party.organisation.name)
            self.assertEqual(stakeholder["PD_SURNAME"], party.name)
            self.assertEqual(stakeholder["ADDRESS1"], party.address)
            # Ensure the correct EnforcementCheckID object is added for the import xml process
            self._assert_enforcement_type_recorded(stakeholder["SH_ID"], entity_uuid, party.type)

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

        self.assertEqual(stakeholder["ELA_ID"], str(get_enforcement_id(application.pk)))
        self.assertIsNotNone(stakeholder["SH_ID"])
        entity_uuid = enforcement_id_to_uuid(stakeholder["SH_ID"])
        party = application.parties.get(party__id=entity_uuid).party
        self.assertIsNotNone(party)
        self.assertEqual(stakeholder["SH_TYPE"], "CONTACT")
        # Ensure the correct EnforcementCheckID object is added for the import xml process
        self._assert_enforcement_type_recorded(stakeholder["SH_ID"], entity_uuid, party.type)

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

        self.assertEqual(stakeholder["ELA_ID"], str(get_enforcement_id(application.pk)))
        self.assertEqual(stakeholder["SH_ID"], str(get_enforcement_id(site.pk)))
        self.assertEqual(stakeholder["SH_TYPE"], "SOURCE")
        self.assertEqual(stakeholder["COUNTRY"], site.address.country.name)
        self.assertEqual(stakeholder["ORG_NAME"], site.organisation.name)
        self.assertEqual(stakeholder["ADDRESS1"], site.address.address_line_1)
        self.assertEqual(
            stakeholder["ADDRESS2"],
            _get_address_line_2(site.address.address_line_2, site.address.postcode, site.address.city),
        )
        # Ensure the correct EnforcementCheckID object is added for the import xml process
        self._assert_enforcement_type_recorded(stakeholder["SH_ID"], site.pk, EnforcementXMLEntityTypes.SITE)

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

        self.assertEqual(stakeholder["ELA_ID"], str(get_enforcement_id(application.pk)))
        self.assertEqual(stakeholder["SH_ID"], str(get_enforcement_id(location.pk)))
        self.assertEqual(stakeholder["SH_TYPE"], "SOURCE")
        self.assertEqual(stakeholder["COUNTRY"], location.country.name)
        self.assertEqual(stakeholder["ORG_NAME"], location.organisation.name)
        self.assertEqual(stakeholder["ADDRESS1"], location.address)
        # Ensure the correct EnforcementCheckID object is added for the import xml process
        self._assert_enforcement_type_recorded(stakeholder["SH_ID"], location.pk, EnforcementXMLEntityTypes.SITE)

    def test_export_xml_organisation_only_success(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, parties=False, site=False)
        application.queues.set([self.queue])
        application.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = ElementTree.fromstring(response.content.decode("utf-8"))  # nosec
        stakeholder = self._xml_to_dict(data[0])

        self.assertEqual(stakeholder["ELA_ID"], str(get_enforcement_id(application.pk)))
        self.assertIsNotNone(stakeholder["SH_ID"], str(get_enforcement_id(self.organisation.pk)))
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
        # Ensure the correct EnforcementCheckID object is added for the import xml process
        self._assert_enforcement_type_recorded(
            stakeholder["SH_ID"], self.organisation.pk, EnforcementXMLEntityTypes.ORGANISATION
        )

    def test_export_xml_no_permission_failure(self):
        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_xml_no_cases_in_queue(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation)
        application.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)
        queue = self.create_queue("Other", self.team)
        application.queues.set([queue])

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_export_xml_no_cases_with_flag_in_queue(self):
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation)
        application.queues.set([self.queue])

        response = self.client.get(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
