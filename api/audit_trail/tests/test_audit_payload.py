from parameterized import parameterized

from api.audit_trail.enums import AuditType
from test_helpers.clients import DataTestClient
from api.audit_trail.payload import format_payload


class TestPayload(DataTestClient):
    @parameterized.expand(
        [
            [AuditType.ADD_FLAGS, {"added_flags": "Flag 1, Flag 2"}, "added the flags 'Flag 1' and 'Flag 2'."],
            [AuditType.MOVE_CASE, {"queues": "Queue 1, Queue 2"}, "moved the case to Queue 1, Queue 2."],
            [AuditType.REMOVE_CASE, {"queues": "Queue 1, Queue 2"}, "removed case from queues: Queue 1, Queue 2."],
            [
                AuditType.UPLOAD_PARTY_DOCUMENT,
                {"file_name": "file.png", "party_type": "third_party", "party_name": "Test technologies"},
                "uploaded the document file.png for third party Test technologies",
            ],
            [AuditType.COUNTERSIGN_ADVICE, {"department": "Test Dept"}, "countersigned all Test Dept recommendations."],
            [AuditType.COUNTERSIGN_ADVICE, {}, "countersigned all  recommendations."],
        ]
    )
    def test_audit_type_formatter_success(self, verb, payload, expected_text):
        text = format_payload(verb, payload)

        self.assertEqual(text, expected_text)

    @parameterized.expand(
        [
            [AuditType.ADD_FLAGS, {"addsadfed_flags": "Flag 1, Flag 2"}, "added_flags"],
            [AuditType.MOVE_CASE, {"queuesadfs": "Queue 1, Queue 2"}, "queues"],
            [AuditType.REMOVE_CASE, {"queuasdfes": "Queue 1, Queue 2"}, "queues"],
            [
                AuditType.UPLOAD_PARTY_DOCUMENT,
                {"filasdfe_name": "file.png", "party_type": "Party", "party_name": "Name"},
                "file_name",
            ],
        ]
    )
    def test_audit_type_formatter_fails(self, verb, payload, key_error):
        with self.assertRaises(Exception) as context:
            format_payload(verb, payload)

        self.assertTrue(key_error in str(context.exception))


@parameterized.expand(
    [
        [{"status": "Submitted"}, "applied for a licence."],
        [{"status": "Resubmitted"}, "reapplied for a licence."],
        [{"status": "applicant_editing"}, "is editing their application."],
        [{"status": "reopened_for_changes"}, "re-opened the application to changes."],
        [{"status": "finalised"}, "updated the status to: finalised."],
        [{"status": "Withdrawn"}, "updated the status to: Withdrawn."],
    ]
)
def test_updated_status(payload, expected_text):
    assert format_payload(AuditType.UPDATED_STATUS, payload) == expected_text
