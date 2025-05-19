from parameterized import parameterized

from django.urls import reverse
from rest_framework import status

from test_helpers.clients import DataTestClient
from api.survey.enums import (
    RecommendationChoiceType,
    ExperiencedIssueEnum,
    HelpfulGuidanceEnum,
    UserAccountEnum,
    UserJourney,
)
from api.survey.tests.factories import SurveyResponseFactory


class SurveyResponseUpdateTests(DataTestClient):

    @parameterized.expand(
        [
            ({},),
            ({"case_type": "00000000-0000-0000-0000-000000000004"},),  # SIEL
            ({"case_type": "00000000-0000-0000-0000-000000000007"},),  # F680
        ]
    )
    def test_update_survey_response(self, request_data):
        survey = SurveyResponseFactory(
            case_type_id=request_data.get("case_type"),
            satisfaction_rating=RecommendationChoiceType.SATISFIED,
            user_journey=UserJourney.APPLICATION_SUBMISSION,
        )
        url = reverse("survey:surveys_update", kwargs={"pk": survey.id})

        data = {
            "url": "N/A",
            "user_journey": UserJourney.APPLICATION_SUBMISSION,
            "satisfaction_rating": RecommendationChoiceType.SATISFIED,
            "satisfaction_rating": RecommendationChoiceType.VERY_SATISFIED,
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
        survey.refresh_from_db()
        for field, expected_value in data.items():
            assert getattr(survey, field) == expected_value, f"Field {field} does not match."
