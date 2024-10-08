import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestChangeTeamRefusalPickList(MigratorTestCase):
    migrate_from = ("letter_templates", "0009_refusal_letter_update_fix")
    migrate_to = ("letter_templates", "0010_refusal_letter_picklist_update_team_ownership")

    def test_refusal_letter_picklist_update_team_ownership(self):
        LICENSING_UNIT_TEAM_ID = "58e77e47-42c8-499f-a58d-94f94541f8c6"  # /PS-IGNORE

        PicklistItem = self.new_state.apps.get_model("picklists", "PicklistItem")

        assert str(PicklistItem.objects.get(name="Refusal letter content").team_id) == LICENSING_UNIT_TEAM_ID
