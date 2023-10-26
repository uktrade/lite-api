from test_helpers.clients import DataTestClient
from api.cases.serializers import CaseDetailSerializer
import datetime
from api.audit_trail.models import (
    Audit,
    AuditType,
)


class CaseDetailSerializerTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation).get_case()

    def test_serializer(self):
        gov_user = self.create_gov_user("test@gmail.com", self.team)  # /PS-IGNORE
        serialized_data = CaseDetailSerializer(self.case, user=gov_user, team=gov_user.team).data
        self.assertEqual(serialized_data["id"], str(self.case.id))
        self.assertIsNotNone(serialized_data["original_submitted_at"])
        self.assertIsNotNone(serialized_data["submitted_at"])

    def test_get_original_submitted_at(self):
        gov_user = self.create_gov_user("test@gmail.com", self.team)  # /PS-IGNORE
        submitted_at_one = CaseDetailSerializer().get_original_submitted_at(self.case)

        self.assertEqual(isinstance(submitted_at_one, datetime.datetime), True)

        self.create_audit(
            verb=AuditType.UPDATED_STATUS,
            actor=self.gov_user,
            target=self.case,
            payload={"status": {"new": "submitted", "old": "draft"}},
        )
        submitted_at_two = CaseDetailSerializer().get_original_submitted_at(self.case)

        # should remain the same because the audit log gets the first value
        self.assertEqual(submitted_at_one, submitted_at_two)

        new_audit = (
            Audit.objects.filter(target_object_id=self.case.id, verb=AuditType.UPDATED_STATUS)
            .order_by("-created_at")
            .first()
        )
        self.assertNotEqual(submitted_at_two, new_audit)

    def test_invalid_get_original_submitted_at(self):
        # this doesn't have a submitted at, and so it will return nothing for the original submitted_at
        case = self.create_draft_standard_application(self.organisation).get_case()
        serialized_data = CaseDetailSerializer().get_original_submitted_at(case)
        self.assertEqual(isinstance(serialized_data, datetime.datetime), False)
