from audit_trail.models import Audit
from audit_trail.payload import AuditType
from test_helpers.clients import DataTestClient
from audit_trail import service


class CasesAuditTrail(DataTestClient):
    # TODO: test schema and creation
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)

    def test_audit_not_deleted(self):
        audit_qs = Audit.objects.all()

        self.assertEqual(audit_qs.count(), 0)

        service.create(actor=self.exporter_user, verb=AuditType.ADD_FLAGS, target=self.case)

        self.assertEqual(audit_qs.count(), 1)

        self.case.delete()

        self.assertEqual(audit_qs.count(), 1)

    def test_retrieve_audit_trail(self):
        service.create(actor=self.exporter_user, verb=AuditType.CREATED_FINAL_ADVICE, target=self.case)

        audit_trail = service.get_obj_trail(self.case)

        self.assertEqual(len(audit_trail), 1)
