from django.core.management import call_command

from api.goods.models import FirearmGoodDetails, FirearmGoodType
from api.goods.tests.factories import FirearmFactory
from test_helpers.clients import DataTestClient


class UpdateSerialNUmberChoiceFieldsMgmtCommandTests(DataTestClient):
    def test_update_sn_choice_fields_command_with_serial_numbers_available(self):
        firearm = FirearmFactory()
        self.assertEqual(firearm.has_identification_markings, True)
        self.assertEqual(firearm.serial_numbers_available, "")

        call_command("update_sn_choice_fields")
        firearm.refresh_from_db()
        self.assertEqual(firearm.serial_numbers_available, FirearmGoodDetails.SN_AVAILABLE)

    def test_update_sn_choice_fields_command_with_serial_numbers_not_available(self):
        firearm = FirearmFactory(
            type=FirearmGoodType.FIREARMS,
            has_identification_markings=False,
            no_identification_markings_details="Products not yet manufactured",
        )
        self.assertEqual(firearm.has_identification_markings, False)
        self.assertEqual(firearm.serial_numbers_available, "")

        call_command("update_sn_choice_fields")
        firearm.refresh_from_db()
        self.assertEqual(firearm.serial_numbers_available, FirearmGoodDetails.SN_NOT_AVAILABLE)
        self.assertEqual(firearm.no_serial_numbers_reason, "Products not yet manufactured")

    def test_update_sn_choice_fields_command_non_core_firearms(self):
        firearm = FirearmFactory(
            type=FirearmGoodType.FIREARMS_ACCESSORY,
            has_identification_markings=False,
            no_identification_markings_details="Products not yet manufactured",
        )
        self.assertEqual(firearm.has_identification_markings, False)
        self.assertEqual(firearm.serial_numbers_available, "")

        call_command("update_sn_choice_fields")
        firearm.refresh_from_db()
        self.assertEqual(firearm.serial_numbers_available, "")
        self.assertEqual(firearm.no_serial_numbers_reason, "")
