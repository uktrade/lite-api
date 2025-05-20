from rest_framework.reverse import reverse
from rest_framework import status
from urllib import parse

from parameterized import parameterized

from api.cases.enums import AdviceType
from test_helpers.clients import DataTestClient


class LetterTemplatesListTests(DataTestClient):

    def setUp(self):
        super().setUp()

    @parameterized.expand(
        [
            [
                {"case_type": "bad_case_type"},
                [],
                [],
                0,
            ],
            [
                {"case_type": "f680_clearance"},
                ["F680 Approval", "F680 Refusal"],
                ["Approve", "Refuse"],
                2,
            ],
            [
                {"case_type": "standard"},
                ["Inform letter", "No licence required letter template", "Refusal letter template", "SIEL template"],
                ["Approve", "Inform", "No Licence Required", "Refuse"],
                4,
            ],
            [
                {"case_type": "open"},
                ["OIEL Approval", "OIEL Refusal"],
                ["Approve", "Refuse"],
                2,
            ],
            [
                {"decision": AdviceType.APPROVE},
                ["SIEL template", "F680 Approval", "OIEL Approval"],
                ["Approve"],
                3,
            ],
            [
                {"case_type": "standard", "decision": AdviceType.APPROVE},
                ["SIEL template"],
                ["Approve"],
                1,
            ],
            [
                {"case_type": "standard", "decision": AdviceType.REFUSE},
                ["Refusal letter template"],
                ["Refuse"],
                1,
            ],
            [
                {"case_type": "open", "decision": AdviceType.APPROVE},
                ["OIEL Approval"],
                ["Approve"],
                1,
            ],
            [
                {"case_type": "open", "decision": AdviceType.REFUSE},
                ["OIEL Refusal"],
                ["Refuse"],
                1,
            ],
            [
                {"case_type": "f680_clearance", "decision": AdviceType.APPROVE},
                ["F680 Approval"],
                ["Approve"],
                1,
            ],
            [
                {"case_type": "f680_clearance", "decision": AdviceType.REFUSE},
                ["F680 Refusal"],
                ["Refuse"],
                1,
            ],
            [
                {"case_type": "standard", "decision": [AdviceType.APPROVE, AdviceType.REFUSE]},
                ["SIEL template", "Refusal letter template"],
                ["Approve", "Refuse"],
                2,
            ],
            [
                {"case_type": "open", "decision": [AdviceType.APPROVE, AdviceType.REFUSE]},
                ["OIEL Approval", "OIEL Refusal"],
                ["Approve", "Refuse"],
                2,
            ],
            [
                {"case_type": "f680_clearance", "decision": [AdviceType.APPROVE, AdviceType.REFUSE]},
                ["F680 Approval", "F680 Refusal"],
                ["Approve", "Refuse"],
                2,
            ],
            [
                {"case_type": "standard", "decision": AdviceType.NO_LICENCE_REQUIRED},
                ["No licence required letter template"],
                ["No Licence Required"],
                1,
            ],
        ]
    )
    def test_letter_templates_list_filter(self, filter, expected_names, expected_decisions, expect_count):

        url = f'{reverse("caseworker_letter_templates:list")}?{parse.urlencode(filter, doseq=True)}'
        response = self.client.get(url, **self.gov_headers)
        response_data = response.json()

        self.assertEqual(len(response_data), expect_count)
        template_names = [item["name"] for item in response_data]
        decisions = list({item["decisions"][0]["name"]["value"] for item in response_data})
        assert sorted(template_names) == sorted(expected_names)
        assert sorted(decisions) == sorted(expected_decisions)

    def test_letter_templates_list_not_allowed(self):

        url = reverse("caseworker_letter_templates:list")
        response = self.client.get(url, **self.exporter_headers, data={})
        assert response.status_code == status.HTTP_403_FORBIDDEN
