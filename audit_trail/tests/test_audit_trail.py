from rest_framework.exceptions import PermissionDenied

from audit_trail import service
from audit_trail.models import Audit
from audit_trail.enums import AuditType
from test_helpers.clients import DataTestClient
from users.models import BaseUser


class CasesAuditTrail(DataTestClient):
    # TODO: test schema and creation
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)

    def test_audit_not_cascade_deleted(self):
        audit_qs = Audit.objects.all()

        self.assertEqual(audit_qs.count(), 0)

        service.create(actor=self.exporter_user, verb=AuditType.ADD_FLAGS, target=self.case)

        self.assertEqual(audit_qs.count(), 1)
        self.case.delete()
        self.assertEqual(audit_qs.count(), 1)

    def test_retrieve_audit_trail(self):
        service.create(actor=self.exporter_user, verb=AuditType.CREATED_FINAL_ADVICE, target=self.case)

        audit_trail_qs = service.get_user_obj_trail_qs(user=self.exporter_user, obj=self.case)

        self.assertEqual(audit_trail_qs.count(), 1)

    def test_invalid_user_cannot_retrieve_audit_trail(self):
        class InvalidUser(BaseUser):
            pass

        user = InvalidUser()

        with self.assertRaises(PermissionDenied):
            service.get_user_obj_trail_qs(user=user, obj=self.case)

    def test_exporter_cannot_retrieve_internal_audit_trail_for_draft(self):
        # Create an audit entry on draft
        service.create(
            actor=self.gov_user, verb=AuditType.CREATED_CASE_NOTE, target=self.case, payload={"case_note": "note"}
        )

        gov_audit_trail_qs = service.get_user_obj_trail_qs(user=self.gov_user, obj=self.case)
        exp_audit_trail_qs = service.get_user_obj_trail_qs(user=self.exporter_user, obj=self.case)

        self.assertEqual(gov_audit_trail_qs.count(), 1)
        self.assertEqual(exp_audit_trail_qs.count(), 0)
