import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestRenameRequestReceived(MigratorTestCase):

    migrate_from = ("statuses", "0008_update_ogd_advice_name")
    migrate_to = ("statuses", "0009_update_request_received_name")

    def test_migration_0008_update_request_received_name(self):
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
                "Appeal received",
                "Senior manager instructions",
                "Pre-circulation",
                "OGD advice",
                "Final decision",
            ]
        )
        assert all_sub_status_names == expected_sub_status_names
