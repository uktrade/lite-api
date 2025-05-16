import pytest

from django.urls import reverse
from rest_framework import status

from api.survey.enums import (
    RecommendationChoiceType,
    ExperiencedIssueEnum,
    HelpfulGuidanceEnum,
    UserAccountEnum,
    UserJourney,
)
from api.survey.models import SurveyResponse
from api.survey.tests.factories import SurveyResponseFactory

pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


@pytest.fixture(scope="function")
def setup(
    hawk_authentication,
):
    return


@pytest.fixture
def hawk_authentication(settings):
    settings.HAWK_AUTHENTICATION_ENABLED = True


@pytest.fixture
def url():
    return reverse("survey:surveys")


class TestSurveyResponseTests:

    @pytest.mark.parametrize(
        "request_data",
        (
            {},
            {"case_type": "00000000-0000-0000-0000-000000000004"},  # SIEL
            {"case_type": "00000000-0000-0000-0000-000000000007"},  # F680
        ),
    )
    def test_create_survey_response(self, get_hawk_client, url, exporter_headers, request_data):
        data = {
            "satisfaction_rating": RecommendationChoiceType.SATISFIED,
            "user_journey": UserJourney.APPLICATION_SUBMISSION,
            **request_data,
        }
        api_client, target_url = get_hawk_client("POST", url, data=data)
        response = api_client.post(target_url, data, **exporter_headers)
        assert response.status_code == status.HTTP_201_CREATED
        actual = response.json()
        survey_response = SurveyResponse.objects.get(id=actual["id"])
        assert actual == {
            "id": str(survey_response.id),
            "satisfaction_rating": RecommendationChoiceType.SATISFIED,
            "case_type": request_data.get("case_type"),
            "user_journey": UserJourney.APPLICATION_SUBMISSION,
        }

    @pytest.mark.parametrize(
        "request_data",
        (
            {},
            {"case_type": "00000000-0000-0000-0000-000000000004"},  # SIEL
            {"case_type": "00000000-0000-0000-0000-000000000007"},  # F680
        ),
    )
    def test_update_survey_response(self, get_hawk_client, exporter_headers, request_data):
        survey = SurveyResponseFactory(
            case_type_id=request_data.get("case_type"),
            satisfaction_rating=RecommendationChoiceType.SATISFIED,
            user_journey=UserJourney.APPLICATION_SUBMISSION,
        )
        url = reverse("survey:surveys_update", kwargs={"pk": survey.id})
        data = {
            "url": "N/A",
            "satisfaction_rating": RecommendationChoiceType.VERY_SATISFIED,
            "experienced_issues": [ExperiencedIssueEnum.NO_ISSUE, ExperiencedIssueEnum.SYSTEM_SLOW],
            "other_detail": "Words",
            "service_improvements_feedback": "Feedback words",
            "guidance_application_process_helpful": HelpfulGuidanceEnum.DISAGREE,
            "process_of_creating_account": UserAccountEnum.EASY,
        }

        api_client, target_url = get_hawk_client("PUT", url, data=data)
        response = api_client.put(target_url, data, **exporter_headers)
        assert response.status_code == status.HTTP_200_OK

        survey.refresh_from_db()
        for field, expected_value in data.items():
            assert getattr(survey, field) == expected_value, f"Field {field} does not match."
