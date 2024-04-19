import pytest

from django_test_migrations.contrib.unittest_case import MigratorTestCase

test_data = [
    {
        "reference": "DN2000/0000",
        "regime_reg_ref": "AB-CD-EF-000",
        "name": "Organisation Name",
        "address": "1000 Street Name, City Name",
        "notifying_government": "Country Name",
        "country": "Country Name",
        "item_list_codes": "0A00100",
        "item_description": "Medium Size Widget",
        "consignee_name": "Example Name",
        "end_use": "Used in industry",
        "reason_for_refusal": "Risk of outcome",
        "spire_entity_id": 123,
        "data": {"END_USER_FLAG": "true", "CONSIGNEE_FLAG": "false", "OTHER_ROLE": ""},
        "entity_type": "",
    },
    {
        "reference": "DN2000/0010",
        "regime_reg_ref": "AB-CD-EF-300",
        "name": "Organisation Name 3",
        "address": "2001 Street Name, City Name 3",
        "notifying_government": "Country Name 3",
        "country": "Country Name 3",
        "item_list_codes": "0A00201",
        "item_description": "Unspecified Size Widget",
        "consignee_name": "Example Name 3",
        "end_use": "Used in other industry",
        "reason_for_refusal": "Risk of outcome 3",
        "spire_entity_id": 125,
        "data": {"END_USER_FLAG": "false", "CONSIGNEE_FLAG": "true", "OTHER_ROLE": ""},
        "entity_type": "",
    },
    {
        "reference": "DN2010/0001",
        "regime_reg_ref": "AB-XY-EF-900",
        "name": "The Widget Company",
        "address": "2 Example Road, Example City",
        "notifying_government": "Example Country",
        "country": "Country Name X",
        "item_list_codes": "catch all",
        "item_description": "Extra Large Size Widget",
        "consignee_name": "Example Name 4",
        "end_use": "Used in unknown industry",
        "reason_for_refusal": "Risk of outcome 4",
        "spire_entity_id": 126,
        "data": {"END_USER_FLAG": "false", "CONSIGNEE_FLAG": "false", "OTHER_ROLE": ""},
        "entity_type": "",
    },
    {
        "reference": "DN3000/0000",
        "regime_reg_ref": "AB-CD-EF-100",
        "name": "Organisation Name XYZ",
        "address": "2000 Street Name, City Name 2",
        "notifying_government": "Country Name 2",
        "country": "Country Name 2",
        "item_list_codes": "0A00200",
        "item_description": "Large Size Widget",
        "consignee_name": "Example Name 2",
        "end_use": "Used in other industry",
        "reason_for_refusal": "Risk of outcome 2",
        "spire_entity_id": 124,
        "data": {"END_USER_FLAG": "false", "CONSIGNEE_FLAG": "false", "OTHER_ROLE": "other"},
        "entity_type": "",
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
        assert DenialEntity.objects.filter(entity_type="End-user").count() == 1
        assert DenialEntity.objects.filter(entity_type="Consignee").count() == 1
        assert DenialEntity.objects.filter(entity_type="Third-party").count() == 2
