from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from django.core.management import call_command
from tempfile import NamedTemporaryFile
import pytest
from django.core.management.base import CommandError
from test_helpers.clients import DataTestClient


class UpdateGoodFromCSVTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)

    def test_update_good_name_from_csv(self):

        new_name = "Bangarang 3000"
        goodonapplication = self.standard_application.goods.get()
        good = goodonapplication.good
        old_name = good.name
        good_id = good.id

        with NamedTemporaryFile(suffix=".csv", delete=True) as tmp_file:
            rows = [
                "good_id,name,new_name,additional_text",
                f"""{good_id},"{old_name}",{new_name},added by John Smith as per LTD-XXX""",
            ]
            tmp_file.write("\n".join(rows).encode("utf-8"))
            tmp_file.flush()

            call_command("update_good_name", tmp_file.name)
            good.refresh_from_db()
            self.assertEqual(good.name, new_name)

            audit = Audit.objects.get()

            self.assertEqual(audit.actor, self.system_user)
            self.assertEqual(audit.target.id, good_id)
            self.assertEqual(audit.verb, AuditType.DEVELOPER_INTERVENTION)
            self.assertEqual(
                audit.payload,
                {
                    "name": {"new": new_name, "old": old_name},
                    "additional_text": "added by John Smith as per LTD-XXX",
                },
            )

    def test_update_good_name_from_csv_invalid(self):

        new_name = "Bangarang 3000"
        goodonapplication = self.standard_application.goods.get()
        good = goodonapplication.good
        old_name = "Definitely not this"
        good_id = good.id

        with NamedTemporaryFile(suffix=".csv", delete=True) as tmp_file:
            rows = [
                "good_id,name,new_name,additional_text",
                f"""{good_id},"{old_name}",{new_name},added by John Smith as per LTD-XXX""",
            ]
            tmp_file.write("\n".join(rows).encode("utf-8"))
            tmp_file.flush()

            with pytest.raises(CommandError):
                call_command("update_good_name", tmp_file.name)
