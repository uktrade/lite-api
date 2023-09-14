import pytest
from django_test_migrations.migrator import Migrator
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestAddCaseSubStatusRecords(MigratorTestCase):

    migrate_from = ("statuses", "0006_casesubstatus")
    migrate_to = ("statuses", "0007_add_case_sub_status_records")

    def test_migration_0007_add_case_sub_status_records(self):
        CaseSubStatus = self.new_state.apps.get_model("statuses", "CaseSubStatus")

        all_sub_statuses = CaseSubStatus.objects.all()

        all_sub_status_names = set([sub_status.name for sub_status in all_sub_statuses])
        expected_sub_status_names = set(
            [
                "Inform letter sent",
                "Refused",
                "Approved",
                "Appeal rejected",
                "Refused after appeal",
                "Approved after appeal",
                "Request received",
                "Senior manager instructions",
                "Pre-circulation",
                "OGD Advice",
                "Final decision",
            ]
        )
        assert all_sub_status_names == expected_sub_status_names
