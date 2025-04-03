from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from django.core.management import call_command
from tempfile import NamedTemporaryFile
import pytest
from api.goods.models import Good
from api.goods.tests.factories import GoodFactory
from test_helpers.clients import DataTestClient
from parameterized import parameterized


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

            with pytest.raises(Good.DoesNotExist):
                call_command("update_good_name", tmp_file.name)

    @parameterized.expand(
        [
            ("This-good\thas-a-tab", "this is the new name"),
            ('This has quotes" and should still match', "this is the new name"),
        ]
    )
    def test_update_good_name_from_csv_escape_character(self, old_goodname, new_goodname):
        good = GoodFactory(name=old_goodname, organisation=self.organisation)
        with NamedTemporaryFile(suffix=".csv", delete=True) as tmp_file:
            rows = [
                "good_id,name,new_name,additional_text",
                f"""{good.id},{good.name},{new_goodname},added by John Smith as per LTD-XXX""",
            ]
            tmp_file.write("\n".join(rows).encode("utf-8"))
            tmp_file.flush()

            call_command("update_good_name", tmp_file.name)
            good.refresh_from_db()
            self.assertEqual(good.name, new_goodname)

            audit = Audit.objects.get()

            self.assertEqual(audit.actor, self.system_user)
            self.assertEqual(audit.target.id, good.id)
            self.assertEqual(audit.verb, AuditType.DEVELOPER_INTERVENTION)
            self.assertEqual(
                audit.payload,
                {
                    "name": {"new": good.name, "old": old_goodname},
                    "additional_text": "added by John Smith as per LTD-XXX",
                },
            )
