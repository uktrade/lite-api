import pytest

from django.urls import reverse
from rest_framework import status

from api.survey.enums import (
    RecommendationChoiceType,
    UserJourney,
)
from api.survey.models import SurveyResponse

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
