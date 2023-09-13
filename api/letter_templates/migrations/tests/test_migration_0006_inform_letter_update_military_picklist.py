import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestChangeInformLetterPickList(MigratorTestCase):

    migrate_from = ("letter_templates", "0005_inform_letter_template_change_advice_type")
    migrate_to = ("letter_templates", "0006_inform_letter_update_military_picklist")


    def test_migration_0006_inform_letter_template_change_picklist_item(self):   
        

        PicklistItem = self.old_state.apps.get_model("picklists", "PicklistItem")

        assert PicklistItem.objects.get(name="Military")



