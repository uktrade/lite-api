from unittest import mock

from django.contrib.contenttypes.models import ContentType
from api.cases.models import Case
from lite_routing.routing_rules_internal.enums import FlagsEnum
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

        service.create(actor=self.exporter_user, verb=AuditType.CREATED, target=self.case)

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

    def test_latest_activities(self):

        qs_1 = Audit.objects.get_latest_activities([self.case.id], 1)
        obj_type = ContentType.objects.get_for_model(Case)
        activity_1 = Audit.objects.get(
            verb=AuditType.UPDATED_STATUS,
            target_object_id=self.case.id,
            target_content_type=obj_type,
        )
        self.assertEqual(activity_1.id, qs_1.first().id)

        activity_1.delete()
        qs_2 = Audit.objects.get_latest_activities([self.case.id], 1)
        assert not qs_2.exists()

        activity_2 = Audit.objects.create(
            actor=self.gov_user,
            verb=AuditType.ADD_CASE_OFFICER_TO_CASE,
            target_object_id=self.case.id,
            target_content_type=ContentType.objects.get_for_model(Case),
            payload={"case_officer": self.gov_user.email},
        )
        qs_3 = Audit.objects.get_latest_activities([self.case.id], 1)
        self.assertEqual(activity_2.id, qs_3.first().id)

        activity_3 = Audit.objects.create(
            actor=self.system_user,
            verb=AuditType.ADDED_FLAG_ON_ORGANISATION,
            action_object_object_id=self.case.id,
            action_object_content_type=ContentType.objects.get_for_model(Case),
            payload={"flag_name": FlagsEnum.AG_CHEMICAL, "additional_text": "additional note here"},
        )
        qs_4 = Audit.objects.get_latest_activities([self.case.id], 2)
        self.assertEqual(activity_3.id, qs_4[0].id)
        self.assertEqual(activity_2.id, qs_4[1].id)

        activity_4 = Audit.objects.create(
            actor=self.system_user,
            verb=AuditType.ADDED_FLAG_ON_ORGANISATION,
            action_object_object_id=self.case.id,
            action_object_content_type=ContentType.objects.get_for_model(Case),
            payload={"flag_name": FlagsEnum.AG_BIOLOGICAL, "additional_text": "additional note here"},
        )
        qs_5 = Audit.objects.get_latest_activities([self.case.id], 2)
        self.assertEqual(activity_4.id, qs_5[0].id)
        self.assertEqual(activity_3.id, qs_5[1].id)
