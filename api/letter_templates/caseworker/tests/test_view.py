from rest_framework.reverse import reverse
from rest_framework import status

from parameterized import parameterized

from api.cases.enums import AdviceType
from api.cases.enums import CaseTypeEnum
from test_helpers.clients import DataTestClient


class LetterTemplatesListTests(DataTestClient):

    def setUp(self):
        super().setUp()

        # We need to shift these out to factories
        self.create_letter_template(
            name="F680 Approval", case_types=[CaseTypeEnum.F680.id], decisions=[AdviceType.ids[AdviceType.APPROVE]]
        )
        self.create_letter_template(
            name="F680 Refusal", case_types=[CaseTypeEnum.F680.id], decisions=[AdviceType.ids[AdviceType.REFUSE]]
        )
        self.create_letter_template(
            name="SIEL Approval", case_types=[CaseTypeEnum.SIEL.id], decisions=[AdviceType.ids[AdviceType.APPROVE]]
        )

        self.create_letter_template(
            name="SIEL Refusal", case_types=[CaseTypeEnum.SIEL.id], decisions=[AdviceType.ids[AdviceType.REFUSE]]
        )

    @parameterized.expand(
        [
            [{"case_type": "f680_clearance"}, ["F680 Approval", "F680 Refusal"], ["Approve", "Refuse"], 2],
            [
                {"decision": "approve"},
                ["SIEL Approval", "F680 Approval"],
                ["Approve"],
                2,
            ],
            [
                {"decision": "approve", "case_type": "f680_clearance"},
                ["F680 Approval"],
                ["Approve"],
                1,
            ],
            [
                {"case_type": "bad_case_type"},
                None,
                None,
                0,
            ],
        ]
    )
    def test_letter_templates_list_filter(self, filter, expected_names, expected_descisions, expect_count):

        url = reverse("caseworker_letter_templates:list")
        response = self.client.get(url, **self.gov_headers, data=filter)
        response_data = response.json()

        self.assertEqual(response_data["count"], expect_count)
        for item in response_data["results"]:
            self.assertTrue(item["name"] in expected_names)
            self.assertTrue(item["decisions"][0]["name"]["value"] in expected_descisions)

    def test_letter_templates_list_not_allowed(self):

        url = reverse("caseworker_letter_templates:list")
        response = self.client.get(url, **self.exporter_headers, data={})
        assert response.status_code == status.HTTP_403_FORBIDDEN
