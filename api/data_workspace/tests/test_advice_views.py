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
        url = reverse("data_workspace:dw-advice")
        response = self.client.get(url)
        payload = response.json()
        last_result = payload["results"][-1]

        # Ensure we get some expected fields
        expected_fields = {"id", "case", "user", "team"}
        assert set(last_result.keys()) == expected_fields
