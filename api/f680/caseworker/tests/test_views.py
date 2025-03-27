import pytest

from django.urls import reverse
from freezegun import freeze_time

from api.f680.enums import RecommendationType, SecurityGrading
from api.f680.models import Recommendation
from api.f680.tests.factories import (
    F680RecipientFactory,
    F680RecommendationFactory,
    F680SecurityReleaseRequestFactory,
    SubmittedF680ApplicationFactory,
)
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.countries.factories import CountryFactory
from api.users.libraries.user_to_token import user_to_token

from lite_routing.routing_rules_internal.enums import TeamIdEnum

pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


@pytest.fixture
def url():
    def _recommendation_url(f680_application):
        return reverse("caseworker_f680:recommendation", kwargs={"pk": f680_application.id})

    return _recommendation_url


@pytest.fixture
def get_f680_application(organisation):

    def _get_f680_application():
        ogd_advice = CaseStatus.objects.get(status=CaseStatusEnum.OGD_ADVICE)
        application = SubmittedF680ApplicationFactory(organisation=organisation, status=ogd_advice)
        recipients = [
            F680RecipientFactory(
                country=CountryFactory(**{"id": "AU", "name": "Australia"}), organisation=organisation
            ),
            F680RecipientFactory(
                country=CountryFactory(**{"id": "NZ", "name": "New Zealand"}), organisation=organisation
            ),
        ]
        for recipient in recipients:
            F680SecurityReleaseRequestFactory(application=application, recipient=recipient)

        return application

    return _get_f680_application


class TestGETRecommendations:

    @freeze_time("2025-01-01 12:00:01")
    def test_GET_recommendation_success(
        self, api_client, get_f680_application, url, team_case_advisor, team_case_advisor_headers
    ):
        f680_application = get_f680_application()
        another_f680_application = get_f680_application()
        gov_user = team_case_advisor(TeamIdEnum.MOD_CAPPROT)

        for release_request in f680_application.security_release_requests.all():
            F680RecommendationFactory(
                case=f680_application,
                security_release_request=release_request,
                type=RecommendationType.APPROVE,
                security_grading="official",
                conditions="No concerns",
            )
        for release_request in another_f680_application.security_release_requests.all():
            F680RecommendationFactory(
                case=another_f680_application, security_release_request=release_request, conditions="No concerns"
            )
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        response = api_client.get(url(f680_application), **headers)
        assert response.status_code == 200
        assert len(response.json()) == f680_application.security_release_requests.count()

        assert Recommendation.objects.count() == (
            f680_application.security_release_requests.count()
            + another_f680_application.security_release_requests.count()
        )

        # check the response shape
        assert response.json() == [
            {
                "id": str(item.id),
                "case": str(item.case.id),
                "type": {"key": "approve", "value": "Approve"},
                "created_at": item.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "security_grading": {"key": "official", "value": "Official"},
                "security_grading_other": item.security_grading_other,
                "conditions": item.conditions,
                "refusal_reasons": item.refusal_reasons,
                "security_release_request": str(item.security_release_request_id),
                "user": {
                    "id": str(item.user.baseuser_ptr.id),
                    "first_name": item.user.baseuser_ptr.first_name,
                    "last_name": item.user.baseuser_ptr.last_name,
                    "team": str(item.user.team.id),
                },
                "team": {
                    "id": str(item.team.id),
                    "name": item.team.name,
                    "alias": item.team.alias,
                },
            }
            for item in Recommendation.objects.filter(case=f680_application)
        ]

    def test_GET_recommendation_raises_notfound_error(
        self, api_client, get_f680_application, team_case_advisor_headers
    ):
        f680_application = get_f680_application()

        for release_request in f680_application.security_release_requests.all():
            F680RecommendationFactory(
                case=f680_application, security_release_request=release_request, conditions="No concerns"
            )
        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        url = reverse("caseworker_f680:recommendation", kwargs={"pk": "138d3a5f-5b5d-457d-8db0-723e14b36de4"})
        response = api_client.get(url, **headers)
        assert response.status_code == 404

    def test_GET_recommendation_raises_forbidden_error(
        self, api_client, get_f680_application, url, team_case_advisor_headers
    ):
        f680_application = get_f680_application()
        for release_request in f680_application.security_release_requests.all():
            F680RecommendationFactory(
                case=f680_application, security_release_request=release_request, conditions="No concerns"
            )
        headers = team_case_advisor_headers(TeamIdEnum.FCDO)
        response = api_client.get(url(f680_application), **headers)
        assert response.status_code == 403


class TestCreateRecommendations:
    def test_POST_recommendation_success(self, api_client, get_f680_application, url, team_case_advisor_headers):
        f680_application = get_f680_application()

        data = [
            {
                "type": RecommendationType.APPROVE,
                "security_grading": SecurityGrading.OFFICIAL_SENSITIVE,
                "conditions": f"Conditions for {rr.recipient.country.name}",
                "refusal_reasons": "",
                "security_release_request": str(rr.id),
            }
            for rr in f680_application.security_release_requests.all()
        ]

        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        response = api_client.post(url(f680_application), data=data, **headers)
        assert response.status_code == 201
        assert f680_application.recommendations.count() == f680_application.security_release_requests.count()

    def test_POST_recommendation_again_raises_error(
        self, api_client, get_f680_application, url, team_case_advisor_headers
    ):
        f680_application = get_f680_application()

        data = [
            {
                "type": RecommendationType.APPROVE,
                "security_grading": SecurityGrading.OFFICIAL_SENSITIVE,
                "conditions": f"Conditions for {rr.recipient.country.name}",
                "refusal_reasons": "",
                "security_release_request": str(rr.id),
            }
            for rr in f680_application.security_release_requests.all()
        ]

        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        response = api_client.post(url(f680_application), data=data, **headers)
        assert response.status_code == 201
        assert f680_application.recommendations.count() == f680_application.security_release_requests.count()

        response = api_client.post(url(f680_application), data=data, **headers)
        assert response.status_code == 403
        assert response.json() == {"errors": {"detail": "You do not have permission to perform this action."}}

    def test_POST_recommendation_another_case_success(self, api_client, get_f680_application, url, team_case_advisor):
        f680_applications = [get_f680_application() for _ in range(4)]
        gov_user = team_case_advisor(TeamIdEnum.MOD_CAPPROT)

        for f680_application in f680_applications:
            data = [
                {
                    "type": RecommendationType.APPROVE,
                    "security_grading": SecurityGrading.OFFICIAL_SENSITIVE,
                    "conditions": f"Conditions for {rr.recipient.country.name}",
                    "refusal_reasons": "",
                    "security_release_request": str(rr.id),
                }
                for rr in f680_application.security_release_requests.all()
            ]
            headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
            response = api_client.post(url(f680_application), data=data, **headers)
            assert response.status_code == 201
            assert f680_application.recommendations.count() == f680_application.security_release_requests.count()

    @pytest.mark.parametrize(
        "data, errors",
        (
            (
                {
                    "security_grading": SecurityGrading.OFFICIAL_SENSITIVE,
                    "conditions": "Conditions for Australia",
                    "refusal_reasons": "",
                },
                [{"type": ["This field is required."]}],
            ),
            (
                {
                    "type": RecommendationType.APPROVE,
                    "conditions": "Conditions for Australia",
                    "refusal_reasons": "",
                },
                [{"security_grading": ["This field is required."]}],
            ),
            (
                {
                    "type": RecommendationType.APPROVE,
                    "refusal_reasons": "",
                    "security_grading": SecurityGrading.OFFICIAL_SENSITIVE,
                },
                [{"conditions": ["This field is required."]}],
            ),
            (
                {
                    "type": RecommendationType.APPROVE,
                    "conditions": "No concerns",
                    "security_grading": SecurityGrading.OFFICIAL_SENSITIVE,
                },
                [{"refusal_reasons": ["This field is required."]}],
            ),
            (
                {
                    "type": RecommendationType.APPROVE,
                    "conditions": "No concerns",
                    "refusal_reasons": "",
                    "security_grading": SecurityGrading.OFFICIAL_SENSITIVE,
                    "security_release_request": "138d3a5f-5b5d-457d-8db0-723e14b36de4",
                },
                [
                    {
                        "security_release_request": [
                            'Invalid pk "138d3a5f-5b5d-457d-8db0-723e14b36de4" - object does not exist.'
                        ]
                    }
                ],
            ),
        ),
    )
    def test_POST_recommendation_validation_errors(
        self, api_client, get_f680_application, url, team_case_advisor_headers, data, errors
    ):
        f680_application = get_f680_application()

        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        release_request = f680_application.security_release_requests.first()
        data = {"security_release_request": str(release_request.id), **data}
        response = api_client.post(url(f680_application), data=[data], **headers)
        assert response.status_code == 400
        assert response.json()["errors"] == errors

    def test_POST_recommendation_invalid_application_raises_error(self, api_client, team_case_advisor_headers):
        url = reverse("caseworker_f680:recommendation", kwargs={"pk": "138d3a5f-5b5d-457d-8db0-723e14b36de4"})
        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        # Data is intentionally empty as we fail before validating the data
        response = api_client.post(url, data=[], **headers)
        assert response.status_code == 404


class TestClearRecommendations:
    def test_DELETE_user_recommendation_success(self, api_client, get_f680_application, url, team_case_advisor):
        f680_application = get_f680_application()
        gov_user = team_case_advisor(TeamIdEnum.MOD_CAPPROT)

        for release_request in f680_application.security_release_requests.all():
            F680RecommendationFactory(
                case=f680_application,
                security_grading=SecurityGrading.OFFICIAL_SENSITIVE,
                security_release_request=release_request,
                conditions="No concerns",
                user=gov_user,
                team=gov_user.team,
            )
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        response = api_client.delete(url(f680_application), **headers)
        assert response.status_code == 204
        assert f680_application.recommendations.count() == 0
