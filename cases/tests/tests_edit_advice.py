from django.urls import reverse
from rest_framework.status import HTTP_201_CREATED

from cases.enums import AdviceType
from cases.models import Advice
from test_helpers.clients import DataTestClient


class EditCaseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_draft_standard_application(self.organisation)
        self.standard_case = self.submit_application(self.standard_application)

        self.open_application = self.create_draft_open_application(self.organisation)
        self.open_case = self.submit_application(self.open_application)

        self.standard_case_url = reverse("cases:case_advice", kwargs={"pk": self.standard_case.id})
        self.open_case_url = reverse("cases:case_advice", kwargs={"pk": self.open_case.id})

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
        }

        self.client.post(self.open_case_url, **self.gov_headers, data=[data])
        self.client.post(self.open_case_url, **self.gov_headers, data=[data])

        # Assert that there's only one piece of advice
        self.assertEqual(Advice.objects.count(), 1)

    def test_standard_case_advice_end_user(self):
        data = {
            "type": AdviceType.APPROVE,
            "text": "I Am Easy to Find",
            "note": "I Am Easy to Find",
            "end_user": str(self.standard_application.end_user.party.id),
        }

        response = self.client.post(self.standard_case_url, **self.gov_headers, data=[data])

        self.assertEqual(response.status_code, HTTP_201_CREATED)
        advice = Advice.objects.get(entity_id=self.standard_application.end_user.party.id)
        self.assertEqual(str(advice.end_user.id), data["end_user"])
        self.assertEqual(advice.entity, advice.end_user)

        entities = Advice.ENTITIES
        entities.remove("end_user")
        for entity in entities:
            self.assertIsNone(getattr(advice, entity, None))
