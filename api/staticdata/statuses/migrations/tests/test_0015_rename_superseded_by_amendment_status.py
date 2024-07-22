import pytest
from django.forms.models import model_to_dict

from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestRenameSupersededByAmendment(MigratorTestCase):

    migrate_from = ("statuses", "0014_remove_casestatus_is_read_only_and_more")
    migrate_to = ("statuses", "0015_rename_superseded_by_amendment_status")

    def test_migration_0013_add_superseded_by_amendment_status(self):
        CaseStatus = self.new_state.apps.get_model("statuses", "CaseStatus")

        STATUS__SUPERSEDED_BY_EXPORTER_EDIT = "00000000-0000-0000-0000-000000000034"
        superseded_by_exporter_edit_status = CaseStatus.objects.get(id=STATUS__SUPERSEDED_BY_EXPORTER_EDIT)
        attributes = model_to_dict(superseded_by_exporter_edit_status)
        assert attributes == {
            "status": "superseded_by_exporter_edit",
            "priority": 34,
            "workflow_sequence": None,
            "next_workflow_status": None,
        }
