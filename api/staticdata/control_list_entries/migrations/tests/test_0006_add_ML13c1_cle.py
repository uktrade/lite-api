import pytest

from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestMigration(MigratorTestCase):
    migrate_from = ("control_list_entries", "0005_adds_5D001e")
    migrate_to = ("control_list_entries", "0006_add_ML13c1_cle")

    def test_add_cle(self):
        ControlListEntry = self.new_state.apps.get_model("control_list_entries", "ControlListEntry")
        parent_cle = ControlListEntry.objects.get(rating="ML13c")
        new_cle = ControlListEntry.objects.get(rating="ML13c1")
        assert new_cle.text == "ML13c1"
        assert new_cle.parent_id == parent_cle.id
        assert new_cle.category == "UK Military List"
        assert new_cle.controlled == True
