import pytest

from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestNCSC(MigratorTestCase):
    migrate_from = ("control_list_entries", "0004_controllistentry_new_entries_20221130")
    migrate_to = ("control_list_entries", "0005_adds_5D001e")

    def test_0005_adds_5D001e(self):
        ControlListEntry = self.old_state.apps.get_model("control_list_entries", "ControlListEntry")

        assert ControlListEntry.objects.filter(rating="5D001e").count() == 1
