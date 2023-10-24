import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestIsRefusalNote(MigratorTestCase):
    migrate_from = ("cases", "0060_case_sub_status")
    migrate_to = ("cases", "0061_case_processing_time")

    def test_0058_advice_is_refusal_note(self):
        CaseModel = self.new_state.apps.get_model("cases", "Case")
        self.assertTrue(hasattr(CaseModel, "processing_time"))

        processing_time = CaseModel._meta.get_field("processing_time")
        self.assertEqual(processing_time.default, 0)

        # We assert that the field did not exist before the migration
        OldCaseModel = self.old_state.apps.get_model("cases", "Case")
        self.assertFalse(hasattr(OldCaseModel, "processing_time"))
