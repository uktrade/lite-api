from django.contrib.contenttypes.models import ContentType
import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase

from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from api.audit_trail.tests.factories import AuditFactory
from test_helpers.clients import DataTestClient


def migrate_status_audit_payloads_for_case(case):
    """Representative of 0002 migration file logic for migrating status payload."""
    content_type = ContentType.objects.get_for_model(case)

    activities = Audit.objects.filter(
        target_object_id=case.id, target_content_type=content_type, verb=AuditType.UPDATED_STATUS
    ).order_by("created_at")

    last_status = None
    for activity in activities:
        if "old" in activity.payload["status"]:
            # all updated for case
            break
        if last_status == None:
            # first status change assumes came from draft
            last_status = activity.payload["status"]
            activity.payload = {"status": {"old": "draft", "new": last_status}}
            activity.save()
            continue
        activity.payload = {"status": {"old": last_status, "new": activity.payload["status"]}}
        activity.save()
        last_status = activity.payload["status"]["new"]


class TestSimpleAuditStatusMigration(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_draft_open_application(self.organisation)
        content_type = ContentType.objects.get_for_model(self.case)

        self.old_payloads = [{"status": "submitted"}, {"status": "applicant_editing"}, {"status": "resubmitted"}]

        self.expected_payloads = [
            {"status": {"new": "submitted", "old": "draft"}},
            {"status": {"new": "applicant_editing", "old": "submitted"}},
            {"status": {"new": "resubmitted", "old": "applicant_editing"}},
        ]

        self.old_audits = [
            AuditFactory(target_content_type=content_type, target_object_id=self.case.id, payload=payload)
            for payload in self.old_payloads
        ]

    def test_migrate_old_status_to_new_status(self):
        migrate_status_audit_payloads_for_case(self.case)
        updated_audit_qs = Audit.objects.filter(
            target_object_id=self.case.id,
            target_content_type=ContentType.objects.get_for_model(self.case),
            verb=AuditType.UPDATED_STATUS,
        ).order_by("created_at")

        for audit, expected_payload in zip(updated_audit_qs, self.expected_payloads):
            self.assertEqual(audit.payload, expected_payload)


class TestMixedAuditStatusMigration(DataTestClient):
    def setUp(self):
        super().setUp()

        self.case = self.create_draft_open_application(self.organisation)
        content_type = ContentType.objects.get_for_model(self.case)

        self.old_payloads = [
            {"status": "submitted"},
            {"status": "applicant_editing"},
            {"status": "resubmitted"},
            {"status": {"new": "applicant_editing", "old": "resubmitted"}},
            {"status": {"new": "withdrawn", "old": "applicant_editing"}},
        ]

        self.expected_payloads = [
            {"status": {"new": "submitted", "old": "draft"}},
            {"status": {"new": "applicant_editing", "old": "submitted"}},
            {"status": {"new": "resubmitted", "old": "applicant_editing"}},
            {"status": {"new": "applicant_editing", "old": "resubmitted"}},
            {"status": {"new": "withdrawn", "old": "applicant_editing"}},
        ]

        self.old_audits = [
            AuditFactory(target_content_type=content_type, target_object_id=self.case.id, payload=payload)
            for payload in self.old_payloads
        ]

    def test_migrate_old_status_to_new_status(self):
        migrate_status_audit_payloads_for_case(self.case)
        updated_audit_qs = Audit.objects.filter(
            target_object_id=self.case.id,
            target_content_type=ContentType.objects.get_for_model(self.case),
            verb=AuditType.UPDATED_STATUS,
        ).order_by("created_at")

        for audit, expected_payload in zip(updated_audit_qs, self.expected_payloads):
            self.assertEqual(audit.payload, expected_payload)


class TestUpdateECJUAuditText(MigratorTestCase):
    migrate_from = ("audit_trail", "0022_alter_audit_verb")
    migrate_to = ("audit_trail", "0023_update_ecju_audit_payload_text")

    def prepare(self):
        """Prepare some data before the migration."""
        Audit = self.old_state.apps.get_model("audit_trail", "Audit")

        self.a_1_payload = {"case_officer": "LITE Testing"}
        self.a_1 = Audit.objects.create(verb="add_case_officer_to_case", payload=self.a_1_payload)
        self.a_2 = Audit.objects.create(verb="ecju_query", payload={"ecju_query": "new query"})
        self.a_3 = Audit.objects.create(
            verb="ecju_query_response", payload={"ecju_response": "I respond to this query"}
        )
        self.a_4 = Audit.objects.create(
            verb="ecju_query_manually_closed", payload={"ecju_response": "I manually closing this query"}
        )

    def test_update_ecju_audit_payload_text(self):
        self.a_1.refresh_from_db()
        self.a_2.refresh_from_db()
        self.a_3.refresh_from_db()
        self.a_4.refresh_from_db()

        assert self.a_1.payload == self.a_1_payload
        assert self.a_2.payload == {"additional_text": "new query"}
        assert self.a_3.payload == {"additional_text": "I respond to this query"}
        assert self.a_4.payload == {"additional_text": "I manually closing this query"}
