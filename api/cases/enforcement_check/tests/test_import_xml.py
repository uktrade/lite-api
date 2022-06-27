import uuid
from uuid import UUID

from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enforcement_check.export_xml import get_enforcement_id
from api.core.constants import GovPermissions
from api.flags.enums import SystemFlags
from lite_content.lite_api.strings import Cases
from test_helpers.clients import DataTestClient


class ImportXML(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("cases:enforcement_check", kwargs={"queue_pk": self.queue.pk})

        # Export
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        self.case = self.create_standard_application_case(self.organisation)
        self.case.queues.set([self.queue])
        self.case.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)

        response = self.client.get(self.url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @staticmethod
    def _build_test_xml(items):
        xml = "<SPIRE_UPLOAD_FILE>"
        for item in items:
            xml += f"<SPIRE_RETURNS><CODE1>{item['code1']}</CODE1><CODE2>{item['code2']}</CODE2><FLAG>{item['flag']}</FLAG></SPIRE_RETURNS>"
        return xml + "</SPIRE_UPLOAD_FILE>"

    def test_import_xml_parties_match_success(self):
        xml = self._build_test_xml(
            [
                {
                    "code1": str(get_enforcement_id(self.case.pk)),
                    "code2": str(get_enforcement_id(party.party_id)),
                    "flag": "Y",
                }
                for party in self.case.parties.all()
            ]
        )

        response = self.client.post(self.url, {"file": xml}, **self.gov_headers)
        self.case.refresh_from_db()
        flags = self.case.flags.values_list("id", flat=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"file": Cases.EnforcementUnit.SUCCESSFUL_UPLOAD})
        self.assertFalse(UUID(SystemFlags.ENFORCEMENT_CHECK_REQUIRED) in flags)
        self.assertTrue(UUID(SystemFlags.ENFORCEMENT_END_USER_MATCH) in flags)
        self.assertTrue(UUID(SystemFlags.ENFORCEMENT_CONSIGNEE_MATCH) in flags)
        self.assertTrue(UUID(SystemFlags.ENFORCEMENT_THIRD_PARTY_MATCH) in flags)
        # Test workflow was not triggered because there was a match
        self.assertFalse(Audit.objects.filter(verb=AuditType.UNASSIGNED).exists())

    def test_import_xml_site_and_org_match_success(self):
        xml = self._build_test_xml(
            [
                {
                    "code1": str(get_enforcement_id(self.case.pk)),
                    "code2": str(get_enforcement_id(self.case.application_sites.first().site_id)),
                    "flag": "Y",
                },
                {
                    "code1": str(get_enforcement_id(self.case.pk)),
                    "code2": str(get_enforcement_id(self.case.organisation.pk)),
                    "flag": "Y",
                },
            ]
        )

        response = self.client.post(self.url, {"file": xml}, **self.gov_headers)
        self.case.refresh_from_db()
        flags = self.case.flags.values_list("id", flat=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"file": Cases.EnforcementUnit.SUCCESSFUL_UPLOAD})
        self.assertFalse(UUID(SystemFlags.ENFORCEMENT_CHECK_REQUIRED) in flags)
        self.assertTrue(UUID(SystemFlags.ENFORCEMENT_SITE_MATCH) in flags)
        self.assertTrue(UUID(SystemFlags.ENFORCEMENT_ORGANISATION_MATCH) in flags)

    def test_import_xml_no_match_success(self):
        xml = self._build_test_xml(
            [
                {
                    "code1": str(get_enforcement_id(self.case.pk)),
                    "code2": str(get_enforcement_id(self.case.organisation.pk)),
                    "flag": "N",
                }
            ]
        )

        response = self.client.post(self.url, {"file": xml}, **self.gov_headers)
        self.case.refresh_from_db()
        flags = self.case.flags.values_list("id", flat=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"file": Cases.EnforcementUnit.SUCCESSFUL_UPLOAD})
        self.assertFalse(UUID(SystemFlags.ENFORCEMENT_CHECK_REQUIRED) in flags)
        self.assertFalse(UUID(SystemFlags.ENFORCEMENT_ORGANISATION_MATCH) in flags)

    def test_import_xml_case_doesnt_match_success(self):
        other_case = self.create_standard_application_case(self.organisation)
        other_case.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)
        xml = self._build_test_xml(
            [
                {
                    "code1": str(get_enforcement_id(self.case.pk)),
                    "code2": str(get_enforcement_id(self.case.organisation.pk)),
                    "flag": "Y",
                }
            ]
        )

        response = self.client.post(self.url, {"file": xml}, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"file": Cases.EnforcementUnit.SUCCESSFUL_UPLOAD})
        self.assertTrue(UUID(SystemFlags.ENFORCEMENT_CHECK_REQUIRED) in other_case.flags.values_list("id", flat=True))

    def test_import_xml_incorrect_format_failure(self):
        xml = "<abc>def</ghi>"
        response = self.client.post(self.url, {"file": xml}, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"file": [Cases.EnforcementUnit.INVALID_FORMAT]}})

    @parameterized.expand(
        [
            "<SPIRE_RETURNS><CODE1>1</CODE1><CODE2>2</CODE2><FLAG>Y</FLAG></SPIRE_RETURNS>",  # no SPIRE_UPLOAD_FILE
            "<SPIRE_UPLOAD_FILE><CODE1>1</CODE1><CODE2>2</CODE2><FLAG>Y</FLAG></SPIRE_UPLOAD_FILE>",  # no SPIRE_RETURNS
            "<SPIRE_UPLOAD_FILE><SPIRE_RETURNS><CODE2></CODE2><FLAG>Y</FLAG></SPIRE_RETURNS></SPIRE_UPLOAD_FILE>",  # no CODE1
            "<SPIRE_UPLOAD_FILE><SPIRE_RETURNS><CODE1></CODE1><FLAG>Y</FLAG></SPIRE_RETURNS></SPIRE_UPLOAD_FILE>",  # no CODE2
            "<SPIRE_UPLOAD_FILE><SPIRE_RETURNS><CODE1></CODE1><CODE2></CODE2></SPIRE_RETURNS></SPIRE_UPLOAD_FILE>",  # no FLAG
            "<SPIRE_UPLOAD_FILE><SPIRE_RETURNS><CODE1></CODE1><CODE2></CODE2><FLAG>Y</FLAG></SPIRE_RETURNS></SPIRE_UPLOAD_FILE>",  # missing CODEs
            "<SPIRE_UPLOAD_FILE><SPIRE_RETURNS><CODE1>1</CODE1><CODE2>2</CODE2><FLAG></FLAG></SPIRE_RETURNS></SPIRE_UPLOAD_FILE>",  # missing FLAG
            "<SPIRE_UPLOAD_FILE><SPIRE_RETURNS><CODE1>1</CODE1><CODE2>2</CODE2><FLAG>a</FLAG></SPIRE_RETURNS></SPIRE_UPLOAD_FILE>",  # invalid FLAG
        ]
    )
    def test_import_xml_incorrect_xml_format_failure(self, xml):
        response = self.client.post(self.url, {"file": xml}, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"file": [Cases.EnforcementUnit.INVALID_XML_FORMAT]}})

    def test_import_xml_invalid_id_failure(self):
        # ID's that don't exist
        xml = self._build_test_xml(
            [
                {
                    "code1": str(get_enforcement_id(self.case.pk)),
                    "code2": 101,
                    "flag": "Y",
                }
            ]
        )

        response = self.client.post(self.url, {"file": xml}, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": {"file": [Cases.EnforcementUnit.INVALID_ID_FORMAT + "101"]}})

    def test_import_xml_invalid_queue_failure(self):
        url = reverse("cases:enforcement_check", kwargs={"queue_pk": uuid.uuid4()})

        response = self.client.post(url, {"file": "abc"}, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
