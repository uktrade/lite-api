from django.urls import reverse
from rest_framework import status

from cases.enums import AdviceType
from cases.models import Advice
from test_helpers.clients import DataTestClient


class ViewCaseAdviceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.standard_application = self.create_standard_application(self.organisation)
        self.standard_case = self.submit_application(self.standard_application)
        self.standard_case_url = reverse("cases:case_advice", kwargs={"pk": self.standard_case.id})

    def test_view_case_advice(self):
        """
        Tests that a gov user can see all advice for a case
        """
        advice = Advice(
            case=self.standard_case,
            user=self.gov_user,
            type=AdviceType.PROVISO,
            proviso="I Am Easy to Proviso",
            text="This is advice",
            note="This is a note",
            end_user=self.standard_application.end_user.party,
        )
        advice.save()

        response = self.client.get(self.standard_case_url, **self.gov_headers)
        response_data = response.json()["advice"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_data), 1)
