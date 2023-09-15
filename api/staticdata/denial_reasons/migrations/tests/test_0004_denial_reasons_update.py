import pytest
import csv
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestUpdateDenialReasons(MigratorTestCase):
    migrate_from = ("denial_reasons", "0003_criterion_1_to_false")
    migrate_to = ("denial_reasons", "0004_denial_reasons_update")

    def test_update_denial_reasons(self):
        DenialReason = self.new_state.apps.get_model("denial_reasons", "DenialReason")
        with open("lite_content/lite_api/denial_reasons_update.csv", "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                dr = DenialReason.objects.get(id=row["id"])
                self.assertEqual(dr.display_value, row["display_value"])

        self.assertEqual(DenialReason.objects.all().count(), 26)
