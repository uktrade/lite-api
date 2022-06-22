from parameterized import parameterized

from api.audit_trail import formatters

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
