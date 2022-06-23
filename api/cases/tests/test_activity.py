from django.urls import reverse

from api.cases.enums import AdviceType, AdviceLevel
from test_helpers.clients import DataTestClient


class ActivityViewTests(DataTestClient):
    def setUp(self):
        super().setUp()
        application = self.create_draft_standard_application(self.organisation)
        self.case = self.submit_application(application)
        self.url = reverse("cases:activity", kwargs={"pk": self.case.id})
        # Give advice to generate some activity from the caseworker
        self.advice_url = reverse("cases:user_advice", kwargs={"pk": self.case.id})
        self.client.post(
            self.advice_url,
            **self.gov_headers,
            data=[
                {
                    "type": AdviceType.APPROVE,
                    "text": "I Am Easy to Find",
                    "note": "I Am Easy to Find",
                    "country": "GB",
                    "level": AdviceLevel.USER,
                }
            ],
        )

    def test_view_pre_submitted_case_notes_post_submit(self):
        response = self.client.get(self.url, **self.gov_headers)
        data = response.json()["activity"]
        assert len(data) == 2
        assert data[0]["user"]["team"] == "Admin"
        assert data[1]["user"]["team"] == ""
