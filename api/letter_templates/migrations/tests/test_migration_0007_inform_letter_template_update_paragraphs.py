import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestChangeInformLetterAdviceType(MigratorTestCase):

    migrate_from = ("letter_templates", "0006_inform_letter_update_military_picklist")
    migrate_to = ("letter_templates", "0007_inform_letter_template_update_paragraphs")

    def test_migration_0006_inform_letter_template_update_paragraphs(self):

        PicklistItem = self.new_state.apps.get_model("picklists", "PicklistItem")
        inform_letter_names = [
            "Weapons of mass destruction (WMD)",
            "Military",
            "Military and weapons of mass destruction (WMD)",
        ]
        # Ensure that the template text has changed as expected
        for name in inform_letter_names:
            pick_list_item = PicklistItem.objects.get(name=name)
            assert "{{addressee.name}}" in pick_list_item.text
