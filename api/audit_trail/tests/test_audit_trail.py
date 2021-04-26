from unittest import mock

from rest_framework.exceptions import PermissionDenied

from api.audit_trail import service
from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from api.audit_trail.serializers import AuditSerializer
from test_helpers.clients import DataTestClient
from api.users.models import BaseUser


class Any(object):
    def __eq__(a, b):
        return True


class CasesAuditTrail(DataTestClient):
    # TODO: test schema and creation
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)

    def test_audit_not_cascade_deleted(self):
        audit_qs = Audit.objects.all()

        self.assertEqual(audit_qs.count(), 1)

        service.create(actor=self.exporter_user, verb=AuditType.ADD_FLAGS, target=self.case)

        self.assertEqual(audit_qs.count(), 2)
        self.case.delete()
        self.assertEqual(audit_qs.count(), 2)

    def test_retrieve_audit_trail(self):
        service.create(actor=self.exporter_user, verb=AuditType.CREATED_FINAL_ADVICE, target=self.case)

        audit_trail_qs = service.get_activity_for_user_and_model(
            user=self.exporter_user.baseuser_ptr, object_type=self.case
        )

        self.assertEqual(audit_trail_qs.count(), 1)

    def test_invalid_user_cannot_retrieve_audit_trail(self):
        class InvalidUser(BaseUser):
            pass

        user = InvalidUser()

        with self.assertRaises(PermissionDenied):
            service.get_activity_for_user_and_model(user=user, object_type=self.case)

    def test_exporter_cannot_retrieve_internal_audit_trail_for_draft(self):
        # Create an audit entry on draft
        service.create(
            actor=self.gov_user, verb=AuditType.CREATED_CASE_NOTE, target=self.case, payload={"additional_text": "note"}
        )

        gov_audit_trail_qs = service.get_activity_for_user_and_model(
            user=self.gov_user.baseuser_ptr, object_type=self.case
        )
        exp_audit_trail_qs = service.get_activity_for_user_and_model(
            user=self.exporter_user.baseuser_ptr, object_type=self.case
        )

        self.assertEqual(gov_audit_trail_qs.count(), 1)
        self.assertEqual(exp_audit_trail_qs.count(), 0)

    @mock.patch("api.audit_trail.signals.logger")
    def test_emit_audit_log(self, mock_logger):
        audit = service.create(actor=self.exporter_user, verb=AuditType.CREATED_FINAL_ADVICE, target=self.case)
        mock_logger.info.assert_called_with(Any(), extra={"audit": AuditSerializer(audit).data})
