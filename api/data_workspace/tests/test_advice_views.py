from django.urls import reverse

from api.cases.enums import AdviceType, AdviceLevel
from test_helpers.clients import DataTestClient


class AdviceDataWorkspaceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(
            self.gov_user,
            self.standard_application,
            "good",
            AdviceType.APPROVE,
            AdviceLevel.FINAL,
            advice_text="advice_text",
        )

    def test_advice(self):
        url = reverse("data_workspace:dw-advice-list")
        response = self.client.get(url)
        payload = response.json()
        last_result = payload["results"][-1]

        # Ensure we get some expected fields
        expected_fields = {
            "id",
            "type",
            "created_at",
            "updated_at",
            "text",
            "note",
            "level",
            "footnote",
            "footnote_required",
            "proviso",
            "pv_grading",
            "collated_pv_grading",
            "case",
            "user",
            "team",
            "good",
            "goods_type",
            "country",
            "end_user",
            "ultimate_end_user",
            "consignee",
            "third_party",
            "denial_reasons",
            "countersigned_by",
            "countersign_comments",
        }
        assert set(last_result.keys()) == expected_fields


class AdviceDenialReasonsDataWorkspaceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(
            self.gov_user,
            self.standard_application,
            "good",
            AdviceType.REFUSE,
            AdviceLevel.FINAL,
            advice_text="advice_text",
        )

    def test_advice_denial_reason(self):
        url = reverse("data_workspace:dw-advice-denial-reasons-list")
        response = self.client.get(url)
        payload = response.json()
        last_result = payload["results"][-1]

        # Ensure we get some expected fields
        expected_fields = {"id", "advice_id", "denialreason_id"}
        assert set(last_result.keys()) == expected_fields
