from audit_trail.models import Audit
from audit_trail.payload import AuditType
from test_helpers.clients import DataTestClient
from audit_trail import service

class CasesAuditTrail(DataTestClient):
    # TODO: test schema and creation
    def setUp(self):
        super().setUp()
        self.draft = self.create_open_application(self.organisation)

    def test_cases_audit_trail(self):
        assert 1

    def test_audit_not_deleted(self):
        audit_qs = Audit.objects.all()
        draft = self.create_open_application(self.organisation)

        self.assertEqual(audit_qs.count(), 0)

        service.create(actor=self.exporter_user, verb=AuditType.ADD_FLAGS, target=draft)

        self.assertEqual(audit_qs.count(), 1)

        draft.delete()

        self.assertEqual(audit_qs.count(), 1)
