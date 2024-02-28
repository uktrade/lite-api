from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from api.survey.models import SurveyResponse
from api.survey.enums import RecommendationChoiceType, ExperiencedIssueEnum, HelpfulGuidanceEnum, UserAccountEnum


class SurveyCreateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.survey = SurveyResponse.objects.create(
            recommendation=RecommendationChoiceType.SATISFIED,
        )

    def test_create_survey(self):
        url = reverse("survey:surveys")
        data = {
            "recommendation": RecommendationChoiceType.SATISFIED,
        }

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["recommendation"], RecommendationChoiceType.SATISFIED)
        survey_response = SurveyResponse.objects.get(id=response_data["id"])
        self.assertEqual(survey_response.recommendation, RecommendationChoiceType.SATISFIED)

    def test_update_survey(self):
        url = reverse("survey:surveys_update", kwargs={"pk": self.survey.id})
        data = {
            "recommendation": RecommendationChoiceType.SATISFIED,
            "other_detail": "Words",
            "experienced_issue": [ExperiencedIssueEnum.NO_ISSUE, ExperiencedIssueEnum.SYSTEM_SLOW],
            "helpful_guidance": HelpfulGuidanceEnum.DISAGREE,
            "user_account_process": UserAccountEnum.EASY,
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
