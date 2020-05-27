from uuid import UUID

from django.urls import reverse
from rest_framework import status

from cases.enforcement_check.export_xml import get_enforcement_id
from conf.constants import GovPermissions
from flags.enums import SystemFlags
from test_helpers.clients import DataTestClient


class ImportXML(DataTestClient):
    def setUp(self):
        super().setUp()
        self.url = reverse("cases:enforcement_check", kwargs={"queue_pk": self.queue.pk})

    @staticmethod
    def _build_test_xml(items):
        xml = "<SPIRE_UPLOAD>"
        for item in items:
            xml += f"<SPIRE_RETURNS><CODE1>{item['code1']}</CODE1><CODE2>{item['code2']}</CODE2><FLAG>{item['flag']}</FLAG></SPIRE_RETURNS>"
        return xml + "</SPIRE_UPLOAD>"

    def test_import_xml_success(self):
        # Export
        self.gov_user.role.permissions.set([GovPermissions.ENFORCEMENT_CHECK.name])
        application = self.create_standard_application_case(self.organisation, site=False)
        application.queues.set([self.queue])
        application.flags.add(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)

        response = self.client.get(self.url, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Import
        xml = self._build_test_xml(
            [
                {
                    "code1": str(get_enforcement_id(application.pk)),
                    "code2": str(get_enforcement_id(party.party_id)),
                    "flag": "Y",
                }
                for party in application.parties.all()
            ]
        )
        response = self.client.post(self.url, {"file": xml}, **self.gov_headers)
        application.refresh_from_db()
        flags = application.flags.values_list("id", flat=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"file": "successful upload"})
        self.assertFalse(UUID(SystemFlags.ENFORCEMENT_CHECK_REQUIRED) in flags)
        self.assertTrue(UUID(SystemFlags.ENFORCEMENT_END_USER_MATCH) in flags)
        self.assertTrue(UUID(SystemFlags.ENFORCEMENT_CONSIGNEE_MATCH) in flags)
        self.assertTrue(UUID(SystemFlags.ENFORCEMENT_THIRD_PARTY_MATCH) in flags)
