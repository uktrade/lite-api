from parameterized import parameterized

from api.audit_trail import formatters
from api.cases.enums import AdviceType
from api.parties.enums import PartyType

from test_helpers.clients import DataTestClient


class FormattersTest(DataTestClient):
    @parameterized.expand(
        [
            ({"removed_flags": "flag1"}, "removed the flag 'flag1'."),
            ({"removed_flags": "flag1, flag2"}, "removed the flags 'flag1' and 'flag2'."),
            (
                {"removed_flags": "flag1, flag2, flag3"},
                "removed the flags 'flag1', 'flag2' and 'flag3'.",
            ),
        ]
    )
    def test_remove_flags(self, payload, expected_result):
        result = formatters.remove_flags(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            ({"added_flags": "flag1"}, "added the flag 'flag1'."),
            ({"added_flags": "flag1, flag2"}, "added the flags 'flag1' and 'flag2'."),
            (
                {"added_flags": "flag1, flag2, flag3"},
                "added the flags 'flag1', 'flag2' and 'flag3'.",
            ),
        ]
    )
    def test_add_flags(self, payload, expected_result):
        result = formatters.add_flags(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            ({"removed_flags": "flag1", "good_name": "good1"}, "removed the flag 'flag1' from the good 'good1'."),
            (
                {"removed_flags": "flag1, flag2", "good_name": "good1"},
                "removed the flags 'flag1' and 'flag2' from the good 'good1'.",
            ),
            (
                {"removed_flags": "flag1, flag2, flag3", "good_name": "good1"},
                "removed the flags 'flag1', 'flag2' and 'flag3' from the good 'good1'.",
            ),
        ]
    )
    def test_remove_good_flags(self, payload, expected_result):
        result = formatters.good_remove_flags(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {"added_flags": "flag1", "good_name": "good1"},
                "added the flag 'flag1' from the good 'good1'.",
            ),
            (
                {"added_flags": "flag1, flag2", "good_name": "good1"},
                "added the flags 'flag1' and 'flag2' from the good 'good1'.",
            ),
            (
                {"added_flags": "flag1, flag2, flag3", "good_name": "good1"},
                "added the flags 'flag1', 'flag2' and 'flag3' from the good 'good1'.",
            ),
        ]
    )
    def test_add_good_flags(self, payload, expected_result):
        result = formatters.good_add_flags(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {"added_flags": "add1", "removed_flags": "remove1", "good_name": "good1"},
                "added the flag 'add1' and removed the flag 'remove1' from the good 'good1'.",
            ),
            (
                {"added_flags": "add1, add2", "removed_flags": "remove1", "good_name": "good1"},
                "added the flags 'add1' and 'add2' and removed the flag 'remove1' from the good 'good1'.",
            ),
            (
                {"added_flags": "add1", "removed_flags": "remove1, remove2", "good_name": "good1"},
                "added the flag 'add1' and removed the flags 'remove1' and 'remove2' from the good 'good1'.",
            ),
            (
                {"added_flags": "add1, add2, add3", "removed_flags": "remove1", "good_name": "good1"},
                "added the flags 'add1', 'add2' and 'add3' and removed the flag 'remove1' from the good 'good1'.",
            ),
        ]
    )
    def test_add_remove_good_flags(self, payload, expected_result):
        result = formatters.good_add_remove_flags(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {"removed_flags": "flag1", "destination_name": "SPECIAL SERVICE CENTRE"},
                "removed the flag 'flag1' from the destination 'Special Service Centre'.",
            ),
            (
                {"removed_flags": "flag1, flag2", "destination_name": "SPECIAL SERVICE CENTRE"},
                "removed the flags 'flag1' and 'flag2' from the destination 'Special Service Centre'.",
            ),
            (
                {"removed_flags": "flag1, flag2, flag3", "destination_name": "SPECIAL SERVICE CENTRE"},
                "removed the flags 'flag1', 'flag2' and 'flag3' from the destination 'Special Service Centre'.",
            ),
        ]
    )
    def test_remove_destination_flags(self, payload, expected_result):
        result = formatters.destination_remove_flags(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {"added_flags": "flag1", "destination_name": "SPECIAL SERVICE CENTRE"},
                "added the flag 'flag1' to the destination 'Special Service Centre'.",
            ),
            (
                {"added_flags": "flag1, flag2", "destination_name": "SPECIAL SERVICE CENTRE"},
                "added the flags 'flag1' and 'flag2' to the destination 'Special Service Centre'.",
            ),
            (
                {"added_flags": "flag1, flag2, flag3", "destination_name": "SPECIAL SERVICE CENTRE"},
                "added the flags 'flag1', 'flag2' and 'flag3' to the destination 'Special Service Centre'.",
            ),
        ]
    )
    def test_add_destination_flags(self, payload, expected_result):
        result = formatters.destination_add_flags(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {"file_name": "test.pdf", "party_type": PartyType.END_USER, "party_name": "Test technologies ltd"},
                "uploaded the document test.pdf for end-user Test technologies ltd.",
            ),
            (
                {
                    "file_name": "test.pdf",
                    "party_type": PartyType.ULTIMATE_END_USER,
                    "party_name": "Test technologies ltd",
                },
                "uploaded the document test.pdf for ultimate end-user Test technologies ltd.",
            ),
            (
                {"file_name": "test.pdf", "party_type": PartyType.THIRD_PARTY, "party_name": "Test technologies ltd"},
                "uploaded the document test.pdf for third party Test technologies ltd.",
            ),
            (
                {
                    "file_name": "test.pdf",
                    "party_type": PartyType.ADDITIONAL_CONTACT,
                    "party_name": "Test technologies ltd",
                },
                "uploaded the document test.pdf for additional contact Test technologies ltd.",
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
                "added the end-user Test technologies ltd.",
            ),
            (
                {"party_type": PartyType.ULTIMATE_END_USER, "party_name": "Test technologies ltd"},
                "added the ultimate end-user Test technologies ltd.",
            ),
            (
                {"party_type": PartyType.THIRD_PARTY, "party_name": "Test technologies ltd"},
                "added the third party Test technologies ltd.",
            ),
            (
                {"party_type": PartyType.ADDITIONAL_CONTACT, "party_name": "Test technologies ltd"},
                "added the additional contact Test technologies ltd.",
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
                "removed the end-user Test technologies ltd.",
            ),
            (
                {"party_type": PartyType.ULTIMATE_END_USER, "party_name": "Test technologies ltd"},
                "removed the ultimate end-user Test technologies ltd.",
            ),
            (
                {"party_type": PartyType.THIRD_PARTY, "party_name": "Test technologies ltd"},
                "removed the third party Test technologies ltd.",
            ),
            (
                {"party_type": PartyType.ADDITIONAL_CONTACT, "party_name": "Test technologies ltd"},
                "removed the additional contact Test technologies ltd.",
            ),
        ]
    )
    def test_remove_party_audit_message(self, payload, expected_result):
        result = formatters.remove_party(**payload)

    @parameterized.expand(
        [
            ({"status": "issued", "licence": "1"}, "issued licence 1."),
            ({"status": "reinstated", "licence": "1"}, "reinstated licence 1."),
            ({"status": "revoked", "licence": "1"}, "revoked licence 1."),
            ({"status": "surrendered", "licence": "1"}, "surrendered licence 1."),
            ({"status": "suspended", "licence": "1"}, "suspended licence 1."),
            (
                {"status": "exhausted", "licence": "1"},
                "The products for licence 1 were exported and the status set to 'exhausted'.",
            ),
            ({"status": "expired", "licence": "1"}, "expired licence 1."),
            ({"status": "draft", "licence": "1"}, "draft licence 1."),
            ({"status": "expired", "licence": "1"}, "expired licence 1."),
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
                "Regimes: No change from 'No regimes'\n"
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
                "Regimes: No change from 'No regimes'\n"
                "Report summary: No change from 'Sniper rifles (10)'",
            ),
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
                    "old_regime_entries": "REGIME1",
                    "new_regime_entries": "REGIME2",
                },
                "reviewed the line 1 assessment for Sniper rifles\n"
                "Licence required: Changed from 'No' to 'Yes'\n"
                "Control list entry: Changed from 'ML8a' to 'ML8b'\n"
                "Regimes: Changed from 'REGIME1' to 'REGIME2'\n"
                "Report summary: Changed from 'None' to 'Sniper rifles (10)'",
            ),
        ]
    )
    def test_product_reviewed_audit_message(self, payload, expected_result):
        result = formatters.product_reviewed(**payload)

    @parameterized.expand(
        [
            (
                {"start_date": "2022-03-02", "licence_duration": "1"},
                "issued licence for 1 month, starting from 2 March 2022.",
            ),
            (
                {"start_date": "2022-03-02", "licence_duration": "24"},
                "issued licence for 24 months, starting from 2 March 2022.",
            ),
        ]
    )
    def test_granted_application(self, payload, expected_result):
        result = formatters.granted_application(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {"start_date": "2022-03-02", "licence_duration": "1"},
                "reinstated licence for 1 month, starting from 2 March 2022.",
            ),
            (
                {"start_date": "2022-03-02", "licence_duration": "24"},
                "reinstated licence for 24 months, starting from 2 March 2022.",
            ),
        ]
    )
    def test_reinstated_application(self, payload, expected_result):
        result = formatters.reinstated_application(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {
                    "product_name": "Sniper rifle",
                    "licence_reference": "GBSIEL/2022/0000001/P",
                    "usage": 1,
                    "quantity": 1,
                },
                "The Sniper rifle product on licence GBSIEL/2022/0000001/P was exported.",
            ),
            (
                {
                    "product_name": "Sniper rifle",
                    "licence_reference": "GBSIEL/2022/0000001/P",
                    "usage": 1,
                    "quantity": 5,
                },
                "1 of 5 Sniper rifle products on licence GBSIEL/2022/0000001/P were exported.",
            ),
            (
                {
                    "product_name": "Sniper rifle",
                    "licence_reference": "GBSIEL/2022/0000001/P",
                    "usage": 5,
                    "quantity": 5,
                },
                "All Sniper rifle products on licence GBSIEL/2022/0000001/P were exported.",
            ),
        ]
    )
    def test_update_product_usage_data(self, payload, expected_result):
        result = formatters.update_product_usage_data(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {
                    "case_reference": "GBSIEL/2022/0000001/P",
                    "licence_reference": "GBSIEL/2022/0000001/P",
                    "decision": AdviceType.APPROVE,
                },
                "added a decision of licence approved.",
            ),
            (
                {
                    "case_reference": "GBSIEL/2022/0000001/P",
                    "licence_reference": "GBSIEL/2022/0000001/P",
                    "decision": AdviceType.REFUSE,
                },
                "added a decision of licence refused.",
            ),
            (
                {
                    "case_reference": "GBSIEL/2022/0000001/P",
                    "licence_reference": "GBSIEL/2022/0000001/P",
                    "decision": AdviceType.NO_LICENCE_REQUIRED,
                },
                "added a decision of no licence needed.",
            ),
            (
                {
                    "case_reference": "GBSIEL/2022/0000001/P",
                    "licence_reference": "GBSIEL/2022/0000001/P",
                    "decision": AdviceType.PROVISO,
                },
                "added a decision proviso.",
            ),
        ]
    )
    def test_create_final_recommendation(self, payload, expected_result):
        result = formatters.create_final_recommendation(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {
                    "case_reference": "GBSIEL/2022/0000001/P",
                    "decision": AdviceType.REFUSE,
                },
                "created a refusal letter.",
            ),
            (
                {
                    "case_reference": "GBSIEL/2022/0000001/P",
                    "decision": AdviceType.INFORM,
                },
                "created an inform letter.",
            ),
            (
                {
                    "case_reference": "GBSIEL/2022/0000001/P",
                    "decision": AdviceType.NO_LICENCE_REQUIRED,
                },
                "created a 'no licence required' letter.",
            ),
            (
                {
                    "case_reference": "GBSIEL/2022/0000001/P",
                    "decision": AdviceType.APPROVE,
                },
                "invalid decision approve for this event.",
            ),
        ]
    )
    def test_generate_decision_letter(self, payload, expected_result):
        result = formatters.generate_decision_letter(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            (
                {
                    "case_reference": "GBSIEL/2022/0000001/P",
                    "decision": AdviceType.INFORM,
                },
                "sent an inform letter.",
            ),
            (
                {
                    "case_reference": "GBSIEL/2022/0000001/P",
                    "decision": AdviceType.APPROVE,
                },
                "invalid decision approve for this event.",
            ),
        ]
    )
    def test_decision_letter_sent(self, payload, expected_result):
        result = formatters.decision_letter_sent(**payload)
        self.assertEqual(result, expected_result)

    @parameterized.expand(
        [
            # Test cases: (flags, action, destination_name, expected_message)
            (["A"], "removed", None, "removed the flag 'A'."),
            (["A", "B"], "removed", None, "removed the flags 'A' and 'B'."),
            (["A"], "removed", "Dest", "removed the flag 'A' from the destination 'Dest'."),
            (["A", "B"], "removed", "Dest", "removed the flags 'A' and 'B' from the destination 'Dest'."),
            (["A", "B", "C"], "removed", "Dest", "removed the flags 'A', 'B' and 'C' from the destination 'Dest'."),
            (["A"], "added", None, "added the flag 'A'."),
            (["A", "B"], "added", None, "added the flags 'A' and 'B'."),
            (["A"], "added", "Dest", "added the flag 'A' to the destination 'Dest'."),
            (["A", "B"], "added", "Dest", "added the flags 'A' and 'B' to the destination 'Dest'."),
            (["A", "B", "C"], "added", "Dest", "added the flags 'A', 'B' and 'C' to the destination 'Dest'."),
        ]
    )
    def test_format_flags_message(self, flags, action, destination_name, expected_message):
        result = formatters.format_flags_message(flags, action, destination_name)
        self.assertEqual(result, expected_message)

    @parameterized.expand(
        [
            (AdviceType.APPROVE, " added a recommendation to approve."),
            (AdviceType.REFUSE, " added a recommendation to refuse."),
            (AdviceType.PROVISO, " added a licence condition."),
        ]
    )
    def test_create_lu_advice(self, advice_status, expected_text):
        result = formatters.create_lu_advice(advice_status)
        assert result == expected_text

    @parameterized.expand(
        [
            (AdviceType.APPROVE, " edited their approval reason."),
            (AdviceType.REFUSE, " edited their refusal reason."),
            (AdviceType.PROVISO, " edited a licence condition."),
        ]
    )
    def test_update_lu_advice(self, advice_status, expected_text):
        result = formatters.update_lu_advice(advice_status, other_param="ignore_other_params")  # /PS-IGNORE
        assert result == expected_text

    @parameterized.expand(
        [
            ("DIT", 1, True, " countersigned all DIT recommendations."),
            ("MOD", 1, True, " countersigned all MOD recommendations."),
            ("DIT", 1, False, " declined to countersign DIT recommendations."),
            ("MOD", 1, False, " declined to countersign MOD recommendations."),
            ("DIT", 2, True, " senior countersigned all DIT recommendations."),
            ("MOD", 2, True, " senior countersigned all MOD recommendations."),
            ("DIT", 2, False, " declined to senior countersign DIT recommendations."),
            ("MOD", 2, False, " declined to senior countersign MOD recommendations."),
        ]
    )
    def test_lu_countersign_advice(self, dept, order, countersign_accepted, expected_text):
        result = formatters.lu_countersign_advice(dept, order, countersign_accepted, other_param="ignore_other_params")
        assert result == expected_text

    @parameterized.expand(
        [
            (AdviceType.REFUSE, " edited their refusal meeting note."),
        ]
    )
    def test_update_lu_meeting_note(self, advice_status, expected_text):
        result = formatters.update_lu_meeting_note(advice_status)
        assert result == expected_text

    @parameterized.expand(
        [
            (AdviceType.REFUSE, " added a refusal meeting note."),
        ]
    )
    def test_create_lu_meeting_note(self, advice_status, expected_text):
        result = formatters.create_lu_meeting_note(advice_status)
        assert result == expected_text
