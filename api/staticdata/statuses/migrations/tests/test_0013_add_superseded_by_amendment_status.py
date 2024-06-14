import pytest
from django.forms.models import model_to_dict

from django_test_migrations.migrator import Migrator
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestSupersededByAmendment(MigratorTestCase):

    migrate_from = ("statuses", "0012_add_draft_rejection_sub_status")
    migrate_to = ("statuses", "0013_add_superseded_by_amendment_status")

    def test_migration_0013_add_superseded_by_amendment_status(self):
        CaseStatus = self.new_state.apps.get_model("statuses", "CaseStatus")

        STATUS__SUPERSEDED_BY_AMENDMENT = "00000000-0000-0000-0000-000000000034"
        superseded_by_amendment_status = CaseStatus.objects.get(id=STATUS__SUPERSEDED_BY_AMENDMENT)
        attributes = model_to_dict(superseded_by_amendment_status)
        assert attributes == {
            "status": "superseded_by_amendment",
            "priority": 34,
            "workflow_sequence": None,
            "is_read_only": True,
            "is_terminal": True,
            "next_workflow_status": None,
        }
