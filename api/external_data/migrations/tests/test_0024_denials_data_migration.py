import pytest

from django_test_migrations.contrib.unittest_case import MigratorTestCase


test_data = [
{"reference":"DN2010\/0057","regime_reg_ref":"reg.123.123","name":"name 1","address":"address 1","notifying_government":"UK","country":"UK","item_list_codes":"all","item_description":"desc a","end_use":"use 1","reason_for_refusal":"a"},
{"reference":"DN2010\/0057","regime_reg_ref":"reg.123.1234","name":"name 2","address":"address 2","notifying_government":"UK","country":"UK","item_list_codes":"all","item_description":"desc a","end_use":"use 1","reason_for_refusal":"a"},
{"reference":"DN2010\/0057","regime_reg_ref":"reg.123.1234","name":"name 3","address":"address 3","notifying_government":"UK","country":"UK","item_list_codes":"all","item_description":"desc a","end_use":"use 1","reason_for_refusal":"a"},
{"reference":"DN2010\/0057","regime_reg_ref":"reg.123.1234","name":"name 4","address":"address 4","notifying_government":"UK","country":"UK","item_list_codes":"all","item_description":"desc a","end_use":"use 1","reason_for_refusal":"a"},
{"reference":"DN2010\/0057","name":"bad record","address":"bad record","notifying_government":"UK","country":"bad","item_list_codes":"all","item_description":"bad","end_use":"bad","reason_for_refusal":"bad "}
]


@pytest.mark.django_db()
class TestDenialDataMigration(MigratorTestCase):

    migrate_from = ("external_data", "0023_set_denial_entity_type")
    migrate_to = ("external_data", "0024_denials_data_migration")


    def prepare(self):
        DenialEntity = self.old_state.apps.get_model("external_data", "DenialEntity")
        for row in test_data:
            DenialEntity.objects.create(**row)  

    


    def test_0023_denials_data_migration(self):
        DenialEntity = self.new_state.apps.get_model("external_data", "DenialEntity")
        Denial = self.new_state.apps.get_model("external_data", "Denial")

        self.assertEqual(DenialEntity.objects.all().count(), 4)
        self.assertEqual(Denial.objects.all().count(), 2)
        self.assertEqual(Denial.objects.get(regime_reg_ref='reg.123.1234').denial_entity.count(), 3)


@pytest.mark.django_db()
class TestDenialDataDuplicatesMigration(MigratorTestCase):

    migrate_from = ("external_data", "0023_set_denial_entity_type")
    migrate_to = ("external_data", "0024_denials_data_migration")


    def prepare(self):
        DenialEntity = self.old_state.apps.get_model("external_data", "DenialEntity")
        for row in test_data:
            DenialEntity.objects.create(**row)
        test_data[0]["end_use"] = "end_use b"
        DenialEntity.objects.create(**test_data[0])
    


    def test_0024_denials_data_migration_duplicates(self):
        DenialEntity = self.new_state.apps.get_model("external_data", "DenialEntity")
        Denial = self.new_state.apps.get_model("external_data", "Denial")
        self.assertEqual(DenialEntity.objects.all().count(),5)
        self.assertEqual(Denial.objects.all().count() == 0)
