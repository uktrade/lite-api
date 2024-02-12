from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from api.survey.models import SurveyResponse
from api.survey.enums import RecommendationChoiceType


class SurveyCreateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.survey = SurveyResponse.objects.create(
            recommendation="SATISFIED",
        )

    def test_create_survey(self):
        url = reverse("survey:surveys")
        data = {
            "recommendation": "SATISFIED",
        }

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["recommendation"], RecommendationChoiceType.SATISFIED)

    def test_update_survey(self):
        url = reverse("survey:surveys_update", kwargs={"pk": self.survey.id})
        data = {
            "recommendation": "SATISFIED",
            "other_detail": "Words",
            "experienced_issue": ["FEATURE", "OTHER"],
            "helpful_guidance": "DISAGREE",
            "user_account_process": "EASY",
            "service_improvements_feedback": "Feedback words",
        }

        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        survey_instance = SurveyResponse.objects.get(id=self.survey.id)
        for field, expected_value in data.items():
            assert getattr(survey_instance, field) == expected_value, f"Field {field} does not match."
