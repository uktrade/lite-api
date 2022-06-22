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


    @parameterized.expand(
        [
            ({"status": "issued", "licence": "1"}, "issued licence 1."),
            ({"status": "Issued", "licence": "1"}, "issued licence 1."),
            ({"status": "reinstated", "licence": "1"}, "reinstated licence 1."),
            ({"status": "cancelled", "licence": "1"}, "cancelled licence 1."),
            ({"status": "withdrawn", "licence": "1"}, "withdrew the licence."),
            ({"status": "Withdrawn", "licence": "1"}, "withdrew the licence."),
        ]
    )
    def test_licence_status_updated(self, payload, expected_result):
        result = formatters.licence_status_updated(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {
                    "line_no": 1,
                    "good_name": "Sniper rifles",
                    "old_is_good_controlled": "No",
                    "new_is_good_controlled": "Yes",
                    "old_control_list_entry": "ML8a",
                    "new_control_list_entry": "ML8b",
                    "old_report_summary": "None",
                    "report_summary": "Sniper rifles (10)",
                },
                "reviewed the line 1 assessment for Sniper rifles\n"
                "Licence required: Changed from 'No' to 'Yes'\n"
                "Control list entry: Changed from 'ML8a' to 'ML8b'\n"
                "Report summary: Changed from 'None' to 'Sniper rifles (10)'",
            ),
            (
                {
                    "line_no": 1,
                    "good_name": "Sniper rifles",
                    "old_is_good_controlled": "No",
                    "new_is_good_controlled": "Yes",
                    "old_control_list_entry": "ML8a",
                    "new_control_list_entry": "ML8a",
                    "old_report_summary": "None",
                    "report_summary": "Sniper rifles (10)",
                },
                "reviewed the line 1 assessment for Sniper rifles\n"
                "Licence required: Changed from 'No' to 'Yes'\n"
                "Control list entry: No change from 'ML8a'\n"
                "Report summary: Changed from 'None' to 'Sniper rifles (10)'",
            ),
            (
                {
                    "line_no": 2,
                    "good_name": "Sniper rifles",
                    "old_is_good_controlled": "No",
                    "new_is_good_controlled": "Yes",
                    "old_control_list_entry": "ML8a",
                    "new_control_list_entry": "ML8b",
                    "old_report_summary": "Sniper rifles (10)",
                    "report_summary": "Sniper rifles (10)",
                },
                "reviewed the line 2 assessment for Sniper rifles\n"
                "Licence required: Changed from 'No' to 'Yes'\n"
                "Control list entry: Changed from 'ML8a' to 'ML8b'\n"
                "Report summary: No change from 'Sniper rifles (10)'",
            ),
        ]
    )
    def test_product_reviewed_audit_message(self, payload, expected_result):
        result = formatters.product_reviewed(**payload)
        self.assertEqual(result, expected_result)
