from uuid import UUID
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.audit_trail.serializers import AuditSerializer
from parameterized import parameterized

from api.cases.models import BadSubStatus
from api.cases.tests.factories import CaseFactory
from api.staticdata.statuses.enums import CaseStatusEnum, CaseSubStatusIdEnum
from api.staticdata.statuses.models import CaseStatus, CaseSubStatus
from api.users.models import ExporterUser
from test_helpers.clients import DataTestClient


class CaseTests(DataTestClient):
    def setUp(self):
        super().setUp()
        application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(application)

    def test_set_sub_status_invalid(self):
        self.assertRaises(BadSubStatus, self.case.set_sub_status, CaseSubStatusIdEnum.FINALISED__APPROVED)

    def test_superseded_by_amendment_exists(self):
        exporter_user = ExporterUser.objects.first()
        amendment = self.case.create_amendment(exporter_user)
        assert self.case.superseded_by == amendment.case_ptr

    def test_superseded_by_no_amendment_exists(self):
        assert self.case.superseded_by == None

    @parameterized.expand(
        [
            ("finalised", CaseSubStatusIdEnum.FINALISED__APPROVED),
            ("finalised", CaseSubStatusIdEnum.FINALISED__REFUSED),
            ("under_final_review", CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT),
        ]
    )
    def test_set_sub_status(self, status, sub_status):
        self.case.status = CaseStatus.objects.get(status=status)
        self.case.save()
        self.case.set_sub_status(sub_status)

        self.case.refresh_from_db()
        assert str(self.case.sub_status.id) == sub_status

        # Check sub status audit
        audit = Audit.objects.filter(verb=AuditType.UPDATED_SUB_STATUS).order_by("-created_at")[0]
        sub_status_name = self.case.sub_status.name
        case_status_name = CaseStatusEnum.get_text(status)
        self.assertEqual(
            audit.payload,
            {"status": case_status_name, "sub_status": sub_status_name},
        )
        audit_text = AuditSerializer(audit).data["text"]
        self.assertEqual(audit_text, f"updated the status to {case_status_name} - {sub_status_name}")

    @parameterized.expand(
        [
            (
                "under_final_review",
                "under_final_review",
                UUID(CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT),
                UUID(CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT),
            ),
            ("under_final_review", "finalised", UUID(CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT), None),
        ]
    )
    def test_case_save_reset_sub_status(self, previous_status, new_status, previous_sub_status, expected_sub_status):
        sub_status = CaseSubStatus.objects.get(id=previous_sub_status)
        case = CaseFactory(
            status=CaseStatus.objects.get(status=previous_status),
            sub_status=sub_status,
        )
        case.refresh_from_db()
        assert case.sub_status == sub_status
        case.status = CaseStatus.objects.get(status=new_status)
        case.save()
        case.refresh_from_db()
        self.assertEqual(case.sub_status_id, expected_sub_status)

    def test_case_save_reset_sub_status_system_audit(self):
        sub_status = CaseSubStatus.objects.get(id=UUID(CaseSubStatusIdEnum.UNDER_FINAL_REVIEW__INFORM_LETTER_SENT))
        case = CaseFactory(
            status=CaseStatus.objects.get(status="under_final_review"),
            sub_status=sub_status,
        )
        case.refresh_from_db()
        assert case.sub_status == sub_status
        case.status = CaseStatus.objects.get(status="finalised")
        case.save()
        case.refresh_from_db()
        self.assertEqual(case.sub_status_id, None)
        # Check add audit
        audit = Audit.objects.get(verb=AuditType.UPDATED_SUB_STATUS)
        self.assertEqual(
            audit.payload,
            {"status": "Finalised", "sub_status": None},
        )
        audit_text = AuditSerializer(audit).data["text"]
        self.assertEqual(audit_text, "updated the status to Finalised")
