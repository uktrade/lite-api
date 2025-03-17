import pytest

from django.urls import reverse

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


def test_GET_recommendation_success(api_client, get_f680_application, team_case_advisor_headers):
    f680_application = get_f680_application()
    another_f680_application = get_f680_application()

    for release_request in f680_application.security_release_requests.all():
        F680RecommendationFactory(
            case=f680_application, security_release_request=release_request, conditions="No concerns"
        )
    for release_request in another_f680_application.security_release_requests.all():
        F680RecommendationFactory(
            case=another_f680_application, security_release_request=release_request, conditions="No concerns"
        )
    url = reverse("caseworker_f680:recommendation", kwargs={"pk": f680_application.id})
    headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
    response = api_client.get(url, **headers)
    assert response.status_code == 200
    assert len(response.json()) == f680_application.security_release_requests.count()

    assert Recommendation.objects.count() == (
        f680_application.security_release_requests.count() + another_f680_application.security_release_requests.count()
    )


def test_POST_recommendation_success(api_client, get_f680_application, team_case_advisor_headers):
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

    url = reverse("caseworker_f680:recommendation", kwargs={"pk": f680_application.id})
    headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
    response = api_client.post(url, data=data, **headers)
    assert response.status_code == 201
    assert f680_application.recommendations.count() == f680_application.security_release_requests.count()


def test_POST_again_clears_previous_recommendation(api_client, get_f680_application, team_case_advisor_headers):
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

    url = reverse("caseworker_f680:recommendation", kwargs={"pk": f680_application.id})
    headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
    response = api_client.post(url, data=data, **headers)
    assert response.status_code == 201
    assert f680_application.recommendations.count() == f680_application.security_release_requests.count()

    recommendation_ids = set(r.id for r in f680_application.recommendations.all())
    response = api_client.post(url, data=data, **headers)
    assert response.status_code == 201
    all_recommendation_ids = set(r.id for r in f680_application.recommendations.all())

    assert bool(all_recommendation_ids.intersection(recommendation_ids)) is False


def test_DELETE_user_recommendation_success(
    api_client, get_f680_application, team_case_advisor, team_case_advisor_headers
):
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
    url = reverse("caseworker_f680:recommendation", kwargs={"pk": f680_application.id})
    headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
    response = api_client.delete(url, **headers)
    assert response.status_code == 204
    assert f680_application.recommendations.count() == 0
