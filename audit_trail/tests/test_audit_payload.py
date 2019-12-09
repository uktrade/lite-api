from parameterized import parameterized

from audit_trail.payload import AuditType
from test_helpers.clients import DataTestClient


class TestPayload(DataTestClient):
    @parameterized.expand(
        [
            [
                AuditType.ADD_FLAGS,
                {'added_flags': 'Flag 1, Flag 2'},
                'added flags: Flag 1, Flag 2'
            ],
            [
                AuditType.MOVE_CASE,
                {'queues': 'Queue 1, Queue 2'},
                'moved the case to: Queue 1, Queue 2'
            ],
            [
                AuditType.REMOVE_CASE,
                {'queues': 'Queue 1, Queue 2'},
                'removed case from queues: Queue 1, Queue 2'
            ],
            [
                AuditType.UPLOAD_PARTY_DOCUMENT,
                {'file_name': 'file.png', 'party_type': 'Party', 'party_name': 'Name'},
                "uploaded the document file.png for Party Name"
            ]
        ]
    )
    def test_audit_type_formatter_success(self, verb, payload, expected_text):
        text = verb.format(payload)

        self.assertEqual(text, expected_text)

    @parameterized.expand(
        [
            [
                AuditType.ADD_FLAGS,
                {'addsadfed_flags': 'Flag 1, Flag 2'},
                'added_flags'
            ],
            [
                AuditType.MOVE_CASE,
                {'queuesadfs': 'Queue 1, Queue 2'},
                'queues'
            ],
            [
                AuditType.REMOVE_CASE,
                {'queuasdfes': 'Queue 1, Queue 2'},
                'queues'
            ],
            [
                AuditType.UPLOAD_PARTY_DOCUMENT,
                {'filasdfe_name': 'file.png', 'party_type': 'Party', 'party_name': 'Name'},
                "file_name"
            ]
        ]
    )
    def test_audit_type_formatter_fails(self, verb, payload, key_error):
        with self.assertRaises(Exception) as context:
            verb.format(payload)

        self.assertTrue(key_error in str(context.exception))
