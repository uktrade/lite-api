from unittest import TestCase

import factory
from django.contrib.contenttypes.models import ContentType

from applications.enums import ApplicationExportType
from applications.models import OpenApplication
from audit_trail.models import Audit
from audit_trail.payload import AuditType
from cases.models import CaseType
from organisations.models import Organisation
from static.statuses.models import CaseStatus


class CaseFactory(factory.django.DjangoModelFactory):
    case_type = CaseType.objects.first()
    export_type = ApplicationExportType.PERMANENT
    status = CaseStatus.objects.first()
    organisation = Organisation.objects.first()

    class Meta:
        model = OpenApplication


class AuditFactory(factory.django.DjangoModelFactory):
    verb = AuditType.UPDATED_STATUS.value

    class Meta:
        model = Audit


def migrate_status_audit_payloads_for_case(case):
    """Duplicated logic from 0002 migration file."""
    content_type = ContentType.objects.get_for_model(case)

    activities = Audit.objects.filter(
        target_object_id=case.id,
        target_content_type=content_type,
        verb=AuditType.UPDATED_STATUS.value
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


class TestSimpleAuditStatusMigration(TestCase):
    def setUp(self):
        self.case = CaseFactory()
        content_type = ContentType.objects.get_for_model(self.case)

        self.old_payloads = [
            {"status": "submitted"},
            {"status": "applicant_editing"},
            {"status": "resubmitted"}
        ]

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
            verb=AuditType.UPDATED_STATUS.value
        ).order_by("created_at")

        for audit, expected_payload in zip(updated_audit_qs, self.expected_payloads):
            self.assertEqual(audit.payload, expected_payload)


class TestMixedAuditStatusMigration(TestCase):
    def setUp(self):
        self.case = CaseFactory()
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
            verb=AuditType.UPDATED_STATUS.value
        ).order_by("created_at")

        for audit, expected_payload in zip(updated_audit_qs, self.expected_payloads):
            self.assertEqual(audit.payload, expected_payload)
