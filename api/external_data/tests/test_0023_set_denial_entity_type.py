import pytest

from django_test_migrations.contrib.unittest_case import MigratorTestCase


test_data = [
    {
        "entity_type": {"END_USER_FLAG": "true", "CONSIGNEE_FLAG": "false", "OTHER_ROLE": ""},
    },
    {
        "entity_type": {"END_USER_FLAG": "false", "CONSIGNEE_FLAG": "true", "OTHER_ROLE": ""},
    },
    {
        "entity_type": {"END_USER_FLAG": "false", "CONSIGNEE_FLAG": "false", "OTHER_ROLE": ""},
    },
    {
        "entity_type": {"END_USER_FLAG": "false", "CONSIGNEE_FLAG": "false", "OTHER_ROLE": "other"},
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
        DenialEntity = self.new_state.apps.get_model("external_data", "DenialEntity")

        assert DenialEntity.objects.all().count() == 4
        assert DenialEntity.objects.get(entity_type="End-user").denial_entity.count() == 1
        assert DenialEntity.objects.get(entity_type="Consignee").denial_entity.count() == 1
        assert DenialEntity.objects.get(entity_type="Third-party").denial_entity.count() == 2
