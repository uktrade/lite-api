from django.urls import reverse

from api.cases.enums import AdviceType, AdviceLevel
from api.cases.models import Advice
from test_helpers.clients import DataTestClient


class EditCaseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.open_application = self.create_draft_open_application(self.organisation)
        self.open_case = self.submit_application(self.open_application)
        self.open_case_url = reverse("cases:user_advice", kwargs={"pk": self.open_case.id})

    def test_edit_standard_case_advice_twice_only_shows_once(self):
        """
        Tests that a gov user cannot create two pieces of advice on the same
        case item (be that a good or destination)
        """
        data = {
            "type": AdviceType.APPROVE,
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "country": "GB",
            "level": AdviceLevel.USER,
        }

        self.client.post(self.open_case_url, **self.gov_headers, data=[data])
        self.client.post(self.open_case_url, **self.gov_headers, data=[data])

        # Assert that there's only one piece of advice
        self.assertEqual(Advice.objects.count(), 1)
