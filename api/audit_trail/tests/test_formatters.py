from parameterized import parameterized

from api.audit_trail import formatters
from api.parties.enums import PartyType

from test_helpers.clients import DataTestClient


class FormattersTest(DataTestClient):
    @parameterized.expand(
        [
            ({"flag_name": ["flag1"]}, "removed the flag 'flag1' from the organisation"),
            ({"flag_name": ["flag1", "flag2"]}, "removed the flags 'flag1' and 'flag2' from the organisation"),
            (
                {"flag_name": ["flag1", "flag2", "flag3"]},
                "removed the flags 'flag1', 'flag2' and 'flag3' from the organisation",
            ),
        ]
    )
    def test_removed_flags(self, payload, expected_result):
        result = formatters.removed_flags(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {"file_name": "test.pdf", "party_type": PartyType.END_USER, "party_name": "Test technologies ltd"},
                "uploaded the document test.pdf for end-user Test technologies ltd",
            ),
            (
                {
                    "file_name": "test.pdf",
                    "party_type": PartyType.ULTIMATE_END_USER,
                    "party_name": "Test technologies ltd",
                },
                "uploaded the document test.pdf for ultimate end-user Test technologies ltd",
            ),
            (
                {"file_name": "test.pdf", "party_type": PartyType.THIRD_PARTY, "party_name": "Test technologies ltd"},
                "uploaded the document test.pdf for third party Test technologies ltd",
            ),
            (
                {
                    "file_name": "test.pdf",
                    "party_type": PartyType.ADDITIONAL_CONTACT,
                    "party_name": "Test technologies ltd",
                },
                "uploaded the document test.pdf for additional contact Test technologies ltd",
            ),
        ]
    )
    def test_upload_party_document_audit_message(self, payload, expected_result):
        result = formatters.upload_party_document(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {"party_type": PartyType.END_USER, "party_name": "Test technologies ltd"},
                "added the end-user Test technologies ltd",
            ),
            (
                {"party_type": PartyType.ULTIMATE_END_USER, "party_name": "Test technologies ltd"},
                "added the ultimate end-user Test technologies ltd",
            ),
            (
                {"party_type": PartyType.THIRD_PARTY, "party_name": "Test technologies ltd"},
                "added the third party Test technologies ltd",
            ),
            (
                {"party_type": PartyType.ADDITIONAL_CONTACT, "party_name": "Test technologies ltd"},
                "added the additional contact Test technologies ltd",
            ),
        ]
    )
    def test_add_party_audit_message(self, payload, expected_result):
        result = formatters.add_party(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {"party_type": PartyType.END_USER, "party_name": "Test technologies ltd"},
                "removed the end-user Test technologies ltd",
            ),
            (
                {"party_type": PartyType.ULTIMATE_END_USER, "party_name": "Test technologies ltd"},
                "removed the ultimate end-user Test technologies ltd",
            ),
            (
                {"party_type": PartyType.THIRD_PARTY, "party_name": "Test technologies ltd"},
                "removed the third party Test technologies ltd",
            ),
            (
                {"party_type": PartyType.ADDITIONAL_CONTACT, "party_name": "Test technologies ltd"},
                "removed the additional contact Test technologies ltd",
            ),
        ]
    )
    def test_remove_party_audit_message(self, payload, expected_result):
        result = formatters.remove_party(**payload)
        self.assertEqual(result, expected_result)
