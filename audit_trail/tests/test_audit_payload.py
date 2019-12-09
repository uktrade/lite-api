from parameterized import parameterized

from audit_trail.payload import AuditType, get_text
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
    def test_get_text(self, verb, payload, expected_text):
        text = get_text(verb, payload)

        self.assertEqual(text, expected_text)
