import pytest

from django_test_migrations.contrib.unittest_case import MigratorTestCase


test_data = [
    {
        "reference": "DN2010\/0057",
        "regime_reg_ref": "reg.123.123",
        "name": "name 1",
        "address": "address 1",
        "notifying_government": "UK",
        "country": "UK",
        "item_list_codes": "all",
        "item_description": "desc a",
        "end_use": "use 1",
        "reason_for_refusal": "a",
        "entity_type": {"end_user_flag": True, "consignee_flag": False},
        "other_role": False,
    },
    {
        "reference": "DN2010\/0057",
        "regime_reg_ref": "reg.123.1234",
        "name": "name 2",
        "address": "address 2",
        "notifying_government": "UK",
        "country": "UK",
        "item_list_codes": "all",
        "item_description": "desc a",
        "end_use": "use 1",
        "reason_for_refusal": "a",
        "entity_type": {"end_user_flag": False, "consignee_flag": True},
        "other_role": False,
    },
    {
        "reference": "DN2010\/0057",
        "regime_reg_ref": "reg.123.1234",
        "name": "name 3",
        "address": "address 3",
        "notifying_government": "UK",
        "country": "UK",
        "item_list_codes": "all",
        "item_description": "desc a",
        "end_use": "use 1",
        "reason_for_refusal": "a",
        "entity_type": {"end_user_flag": False, "consignee_flag": False},
        "other_role": True,
    },
    {
        "reference": "DN2010\/0057",
        "regime_reg_ref": "reg.123.1234",
        "name": "name 4",
        "address": "address 4",
        "notifying_government": "UK",
        "country": "UK",
        "item_list_codes": "all",
        "item_description": "desc a",
        "end_use": "use 1",
        "reason_for_refusal": "a",
        "entity_type": {"end_user_flag": False, "consignee_flag": False},
        "other_role": False,
    },
    {
        "reference": "DN2010\/0057",
        "name": "bad record",
        "address": "bad record",
        "notifying_government": "UK",
        "country": "bad",
        "item_list_codes": "all",
        "item_description": "bad",
        "end_use": "bad",
        "reason_for_refusal": "bad ",
    },
]


@pytest.mark.django_db()
class TestDenialEntityTypeSet(MigratorTestCase):
    migrate_from = ("external_data", "0022_denialentity_entity_type")
    migrate_to = ("external_data", "0023_set_denial_entity_type")

    def prepare(self):
        DenialEntity = self.old_state.apps.get_model("external_data", "DenialEntity")
        for row in test_data:
            DenialEntity.objects.create(**row)

    def test_0023_set_denial_entity_type(self):
        OldDenialEntity = self.old_state.apps.get_model("external_data", "DenialEntity")
        NewDenialEntity = self.new_state.apps.get_model("external_data", "NewDenialEntity")

        assert OldDenialEntity.objects.all().count() == 4
        assert NewDenialEntity.objects.all().count() == 3
        assert NewDenialEntity.objects.get(entity_type="End-user").denial_entity.count() == 1
        assert NewDenialEntity.objects.get(entity_type="Consignee").denial_entity.count() == 1
        assert NewDenialEntity.objects.get(entity_type="Third-party").denial_entity.count() == 1
