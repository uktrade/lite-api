import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestIsRefusalNote(MigratorTestCase):
    migrate_from = ("cases", "0057_auto_20230505_1209")
    migrate_to = ("cases", "0058_advice_is_refusal_note")

    def test_0058_advice_is_refusal_note(self):
        AdviceModel = self.new_state.apps.get_model("cases", "Advice")
        self.assertTrue(hasattr(AdviceModel, "is_refusal_note"))

        is_refusal_note_field = AdviceModel._meta.get_field("is_refusal_note")
        self.assertEqual(is_refusal_note_field.default, False)

        # We assert that the field did not exist before the migration
        OldAdviceModel = self.old_state.apps.get_model("cases", "Advice")
        self.assertFalse(hasattr(OldAdviceModel, "is_refusal_note"))
