from api.audit_trail.tests.factories import AuditFactory
from test_helpers.clients import DataTestClient


class GoodOnApplicationAuditTrailTests(DataTestClient):
    def test_removing_object_keeps_audit_trail(self):
        application = self.create_draft_standard_application(self.organisation)
        good_on_application = application.goods.first()
        audit = AuditFactory(
            action_object=good_on_application,
        )

        good_on_application.delete()
        audit.refresh_from_db()
        self.assertIsNone(audit.action_object)
