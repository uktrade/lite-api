import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestCriterion1ToTrue(MigratorTestCase):
    migrate_from = ("denial_reasons", "0002_denialreason_display_value")
    migrate_to = ("denial_reasons", "0003_criterion_1_to_false")

    def prepare(self):
        DenialReason = self.old_state.apps.get_model("denial_reasons", "DenialReason")
        DenialReason.objects.create(id=1, deprecated=True, display_value="1")

    def test_criterion_1_to_false(self):
        DenialReason = self.new_state.apps.get_model("denial_reasons", "DenialReason")
        denial_reason = DenialReason.objects.get(id=1)
        self.assertFalse(denial_reason.deprecated)
