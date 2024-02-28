from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from api.survey.models import SurveyResponse
from api.survey.enums import (
    RecommendationChoiceType,
    ExperiencedIssueEnum,
    HelpfulGuidanceEnum,
    UserAccountEnum,
    UserJourney,
)


class SurveyCreateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.survey = SurveyResponse.objects.create(
            satisfaction_rating=RecommendationChoiceType.SATISFIED, user_journey=UserJourney.APPLICATION_SUBMISSION
        )

    def test_create_survey(self):
        url = reverse("survey:surveys")
        data = {
            "satisfaction_rating": RecommendationChoiceType.SATISFIED,
            "user_journey": UserJourney.APPLICATION_SUBMISSION,
        }

        response = self.client.post(url, data, **self.exporter_headers)
        response_data = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["satisfaction_rating"], RecommendationChoiceType.SATISFIED)
        survey_response = SurveyResponse.objects.get(id=response_data["id"])
        self.assertEqual(survey_response.satisfaction_rating, RecommendationChoiceType.SATISFIED)

    def test_update_survey(self):
        url = reverse("survey:surveys_update", kwargs={"pk": self.survey.id})
        data = {
            "url": "N/A",
            "user_journey": UserJourney.APPLICATION_SUBMISSION,
            "satisfaction_rating": RecommendationChoiceType.SATISFIED,
            "experienced_issues": [ExperiencedIssueEnum.NO_ISSUE, ExperiencedIssueEnum.SYSTEM_SLOW],
            "other_detail": "Words",
            "service_improvements_feedback": "Feedback words",
            "guidance_application_process_helpful": HelpfulGuidanceEnum.DISAGREE,
            "process_of_creating_account": UserAccountEnum.EASY,
        }

        response = self.client.put(url, data, **self.exporter_headers)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        survey_instance = SurveyResponse.objects.get(id=self.survey.id)
        for field, expected_value in data.items():
            assert getattr(survey_instance, field) == expected_value, f"Field {field} does not match."
