from api.audit_trail.models import Audit
from api.audit_trail.tests.factories import AuditFactory

from test_helpers.clients import DataTestClient


class GoodOnApplicationAuditTrailTests(DataTestClient):
    def test_removing_object_keeps_audit_trail(self):
        application = self.create_draft_standard_application(self.organisation)
        Audit.objects.all().delete()

        good_on_application = application.goods.first()
        audit = AuditFactory(
            action_object=good_on_application,
        )
        self.assertEqual(Audit.objects.count(), 1)

        good_on_application.delete()

        self.assertEqual(Audit.objects.count(), 1)
        audit = Audit.objects.get(pk=audit.pk)
        self.assertIsNone(audit.action_object)
