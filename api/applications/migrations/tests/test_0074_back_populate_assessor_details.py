import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase

from api.audit_trail.enums import AuditType


@pytest.mark.django_db()
class TestBackPopulateProductAssessorDetails(MigratorTestCase):
    migrate_from = ("applications", "0073_auto_20231016_1508")
    migrate_to = ("applications", "0074_back_populate_product_assessor_details")

    def test_0074_populate_product_assessor_details(self):
        # We assert that the fields are not set before the migration
        OldGoodOnApplication = self.old_state.apps.get_model("applications", "GoodOnApplication")
        Audit = self.old_state.apps.get_model("audit_trail", "Audit")
        for item in Audit.objects.filter(verb=AuditType.PRODUCT_REVIEWED).order_by("created_at"):
            good_on_application = OldGoodOnApplication.objects.get(id=item.action_object_object_id)
            self.assertIsNone(good_on_application.assessed_by)
            self.assertIsNone(good_on_application.assessment_date)

        for item in Audit.objects.filter(verb=AuditType.GOOD_REVIEWED).order_by("created_at"):
            good_on_application = OldGoodOnApplication.objects.get(id=item.action_object_object_id)
            self.assertIsNone(good_on_application.assessed_by)
            self.assertIsNone(good_on_application.assessment_date)

        GoodOnApplication = self.new_state.apps.get_model("applications", "GoodOnApplication")
        for item in Audit.objects.filter(verb=AuditType.PRODUCT_REVIEWED).order_by("created_at"):
            good_on_application = GoodOnApplication.objects.get(id=item.action_object_object_id)
            self.assertEqual(good_on_application.assessed_by_id, item.actor_object_id)
            self.assertEqual(good_on_application.assessment_date, item.created_at)

        for item in Audit.objects.filter(verb=AuditType.GOOD_REVIEWED).order_by("created_at"):
            good_on_application = GoodOnApplication.objects.get(id=item.action_object_object_id)
            self.assertEqual(good_on_application.assessed_by_id, item.actor_object_id)
            self.assertEqual(good_on_application.assessment_date, item.created_at)
