from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from django.core.management import call_command
from tempfile import NamedTemporaryFile
import pytest
from api.parties.models import Party
from test_helpers.clients import DataTestClient


class UpdatePartyFromCSVTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)

    def test_update_field_on_party_from_csv(self):

        new_name = "Bangarang 3000"
        old_name = self.standard_application.end_user.party.name
        party_id = self.standard_application.end_user.party.id

        with NamedTemporaryFile(suffix=".csv", delete=True) as tmp_file:
            rows = [
                "party_id,name,new_name,additional_text",
                f"""{party_id},"{old_name}",{new_name},added by John Smith as per LTD-XXX""",
            ]
            tmp_file.write("\n".join(rows).encode("utf-8"))
            tmp_file.flush()

            call_command("update_party_name", tmp_file.name)
            self.standard_application.refresh_from_db()
            self.assertEqual(self.standard_application.end_user.party.name, new_name)

            audit = Audit.objects.get()

            self.assertEqual(audit.actor, self.system_user)
            self.assertEqual(audit.target.id, party_id)
            self.assertEqual(audit.verb, AuditType.DEVELOPER_INTERVENTION)
            self.assertEqual(
                audit.payload,
                {
                    "name": {"new": new_name, "old": old_name},
                    "additional_text": "added by John Smith as per LTD-XXX",
                },
            )

    def test_update_field_on_party_from_csv_invalid(self):

        new_name = "Bangarang 3000"
        old_name = "This is not an name"
        party_id = self.standard_application.end_user.party.id

        with NamedTemporaryFile(suffix=".csv", delete=True) as tmp_file:
            rows = [
                "party_id,name,new_name,additional_text",
                f"""{party_id},"{old_name}",{new_name},added by John Smith as per LTD-XXX""",
            ]
            tmp_file.write("\n".join(rows).encode("utf-8"))
            tmp_file.flush()

            with pytest.raises(Party.DoesNotExist):
                call_command("update_party_name", tmp_file.name)
