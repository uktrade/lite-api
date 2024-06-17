import pytest

from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestPopulateLUCicExistingFlagMigration(MigratorTestCase):

    LICENSING_TEAM_UNIT_ID= '58e77e47-42c8-499f-a58d-94f94541f8c6'
    FLAG_NAME = 'LU Change in Circumstances'

    migrate_from = ("flags", "0006_flag_remove_on_finalised")
    migrate_to = ("flags", "0007_populate_lu_cic_flag")

    def prepare(self):
        Flag = self.old_state.apps.get_model("flags", "Flag")
        Flag.objects.create(
            name = self.FLAG_NAME,
            level = 'Case',
            team_id = self.LICENSING_TEAM_UNIT_ID,
            blocks_finalising=True,
            alias = 'LU_CHANGE_IN_CIRCUMSTANCES',
        )

    def test_0006_populate_lu_cic_flag(self):
        Flag = self.new_state.apps.get_model("flags", "Flag")
        self.assertEqual(Flag.objects.filter(name=self.FLAG_NAME).count(), 1)



@pytest.mark.django_db()
class TestPopulateLUCicFlagMigration(MigratorTestCase):

    LICENSING_TEAM_UNIT_ID= '58e77e47-42c8-499f-a58d-94f94541f8c6'
    FLAG_NAME = 'LU Change in Circumstances'

    migrate_from = ("flags", "0006_flag_remove_on_finalised")
    migrate_to = ("flags", "0007_populate_lu_cic_flag")

    def test_0006_populate_lu_cic_flag(self):
        Flag = self.new_state.apps.get_model("flags", "Flag")
        self.assertEqual(Flag.objects.filter(name=self.FLAG_NAME).count(), 1)