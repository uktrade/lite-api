import pytest
from django_test_migrations.migrator import Migrator
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestCaseSubStatusPopulateOrder(MigratorTestCase):

    migrate_from = ("statuses", "0010_casesubstatus_order")
    migrate_to = ("statuses", "0011_casesubstatus_populate_order")

    def test_migration_0011_casesubstatus_populate_order(self):
        CaseSubStatus = self.new_state.apps.get_model("statuses", "CaseSubStatus")

        all_sub_statuses = CaseSubStatus.objects.all()

        all_sub_status_order = set([(sub_status.name, sub_status.order) for sub_status in all_sub_statuses])
        expected_sub_status_order = set(
            [
                ("Inform letter sent", 0),
                ("Refused", 0),
                ("Approved", 10),
                ("Appeal rejected", 20),
                ("Refused after appeal", 30),
                ("Approved after appeal", 40),
                ("Appeal received", 0),
                ("Senior manager instructions", 10),
                ("Pre-circulation", 20),
                ("OGD advice", 30),
                ("Final decision", 40),
            ]
        )
        assert all_sub_status_order == expected_sub_status_order
