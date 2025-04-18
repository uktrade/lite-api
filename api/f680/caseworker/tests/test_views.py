import pytest

from dateutil.relativedelta import relativedelta
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from api.f680 import enums
from api.f680.models import Recommendation, SecurityReleaseOutcome
from api.f680.tests.factories import (
    F680RecipientFactory,
    F680RecommendationFactory,
    F680SecurityReleaseRequestFactory,
    F680SecurityReleaseOutcomeFactory,
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


SECURITY_RELEASE_REQUEST_IDS = [
    "7ca31d7f-9be7-470b-8a87-c23d495f649d",  # /PS-IGNORE
    "944ed9f5-47ea-4c88-89cf-8cc9f32fb0bb",  # /PS-IGNORE
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
    def _recommendation_url(f680_application):
        return reverse("caseworker_f680:recommendation", kwargs={"pk": f680_application.id})

    return _recommendation_url


@pytest.fixture
def get_f680_application(organisation):

    def _get_f680_application(static_release_request_ids=True):
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

        if static_release_request_ids:
            release_ids = SECURITY_RELEASE_REQUEST_IDS
        else:
            release_ids = [uuid4() for recipient in recipients]

        for request_id, recipient in zip(release_ids, recipients):
            F680SecurityReleaseRequestFactory(id=request_id, application=application, recipient=recipient)

        return application

    return _get_f680_application


class TestF680RecommendationViewSet:
    @freeze_time("2025-01-01 12:00:01")
    def test_GET_recommendation_success(
        self, get_hawk_client, get_f680_application, url, team_case_advisor, team_case_advisor_headers
    ):
        f680_application = get_f680_application()
        another_f680_application = get_f680_application(static_release_request_ids=False)
        gov_user = team_case_advisor(TeamIdEnum.MOD_CAPPROT)

        for release_request in f680_application.security_release_requests.all():
            F680RecommendationFactory(
                case=f680_application,
                security_release_request=release_request,
                type=enums.RecommendationType.APPROVE,
                conditions="No concerns",
            )
        for release_request in another_f680_application.security_release_requests.all():
            F680RecommendationFactory(
                case=another_f680_application, security_release_request=release_request, conditions="No concerns"
            )
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        api_client, target_url = get_hawk_client("GET", url(f680_application))
        response = api_client.get(target_url, **headers)
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
                "case": str(item.case_id),
                "type": {"key": "approve", "value": "Approve"},
                "created_at": item.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "conditions": item.conditions,
                "refusal_reasons": item.refusal_reasons,
                "security_release_request": str(item.security_release_request_id),
                "user": {
                    "id": str(item.user.baseuser_ptr_id),
                    "first_name": item.user.baseuser_ptr.first_name,
                    "last_name": item.user.baseuser_ptr.last_name,
                    "team": str(item.user.team.id),
                },
                "team": {
                    "id": str(item.team_id),
                    "name": item.team.name,
                    "alias": item.team.alias,
                },
            }
            for item in Recommendation.objects.filter(case=f680_application)
        ]

    def test_GET_recommendation_raises_notfound_error(
        self, get_hawk_client, get_f680_application, team_case_advisor_headers
    ):
        f680_application = get_f680_application()

        for release_request in f680_application.security_release_requests.all():
            F680RecommendationFactory(
                case=f680_application, security_release_request=release_request, conditions="No concerns"
            )
        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        url = reverse(
            "caseworker_f680:recommendation", kwargs={"pk": "138d3a5f-5b5d-457d-8db0-723e14b36de4"}  # /PS-IGNORE
        )
        api_client, target_url = get_hawk_client("GET", url)
        response = api_client.get(target_url, **headers)
        assert response.status_code == 404

    def test_f680_cases_list(self, get_hawk_client, get_f680_application, team_case_advisor):
        gov_user = team_case_advisor(TeamIdEnum.MOD_CAPPROT)
        f680_application = get_f680_application()
        for release_request in f680_application.security_release_requests.all():
            F680RecommendationFactory(
                case=f680_application,
                security_release_request=release_request,
                type=enums.RecommendationType.APPROVE,
                user=gov_user,
                team=gov_user.team,
                conditions="No concerns",
            )

        url = reverse("cases:search")
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        api_client, target_url = get_hawk_client("GET", url)
        response = api_client.get(target_url, **headers)
        assert response.status_code == 200
        assert response.json()["count"] == 1
        actual = response.json()["results"]["cases"][0]["f680_data"]

        product = f680_application.get_product()
        assert product.name == actual["product"]["name"]
        assert product.description == actual["product"]["description"]

        for item in actual["security_release_requests"]:
            release_request = f680_application.security_release_requests.get(id=item["id"])
            assert release_request.recipient.country.id == item["recipient"]["country"]["id"]
            assert release_request.recipient.country.name == item["recipient"]["country"]["name"]
            assert release_request.recipient.name == item["recipient"]["name"]
            assert release_request.recipient.type == item["recipient"]["type"]["key"]
            assert release_request.security_grading == item["security_grading"]["key"]
            assert release_request.approval_types == item["approval_types"]
            assert release_request.intended_use == item["intended_use"]

        expected_recommendations = [
            {
                "type": item.type,
                "team": item.team.name,
            }
            for item in Recommendation.objects.filter(case=f680_application).distinct("type", "team")
        ]
        assert expected_recommendations == actual["recommendations"]

    def test_POST_recommendation_success(self, get_hawk_client, get_f680_application, url, team_case_advisor_headers):
        f680_application = get_f680_application()

        data = [
            {
                "type": enums.RecommendationType.APPROVE,
                "conditions": f"Conditions for {rr.recipient.country.name}",
                "refusal_reasons": "",
                "security_release_request": str(rr.id),
            }
            for rr in f680_application.security_release_requests.all()
        ]

        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        api_client, target_url = get_hawk_client("POST", url(f680_application), data=data)
        response = api_client.post(target_url, data, **headers)
        assert response.status_code == 201
        assert f680_application.recommendations.count() == f680_application.security_release_requests.count()

    def test_POST_recommendation_again_raises_no_error(
        self, get_hawk_client, get_f680_application, url, team_case_advisor_headers
    ):
        f680_application = get_f680_application()

        data = [
            {
                "type": enums.RecommendationType.APPROVE,
                "conditions": f"Conditions for {rr.recipient.country.name}",
                "refusal_reasons": "",
                "security_release_request": str(rr.id),
            }
            for rr in f680_application.security_release_requests.all()
        ]

        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        api_client, target_url = get_hawk_client("POST", url(f680_application), data=data[:1])
        response = api_client.post(target_url, data[:1], **headers)
        assert response.status_code == 201
        assert f680_application.recommendations.count() == 1

        api_client, target_url = get_hawk_client("POST", url(f680_application), data=data[1:])
        response = api_client.post(target_url, data[1:], **headers)
        assert response.status_code == 201
        assert f680_application.recommendations.count() == f680_application.security_release_requests.count()

    def test_POST_recommendation_another_case_success(
        self, get_hawk_client, get_f680_application, url, team_case_advisor
    ):
        f680_applications = [get_f680_application(static_release_request_ids=False) for _ in range(4)]
        gov_user = team_case_advisor(TeamIdEnum.MOD_CAPPROT)

        for f680_application in f680_applications:
            data = [
                {
                    "type": enums.RecommendationType.APPROVE,
                    "conditions": f"Conditions for {rr.recipient.country.name}",
                    "refusal_reasons": "",
                    "security_release_request": str(rr.id),
                }
                for rr in f680_application.security_release_requests.all()
            ]
            headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
            api_client, target_url = get_hawk_client("POST", url(f680_application), data=data)
            response = api_client.post(target_url, data, **headers)
            assert response.status_code == 201
            assert f680_application.recommendations.count() == f680_application.security_release_requests.count()

    @pytest.mark.parametrize(
        "data, errors",
        (
            (
                {
                    "conditions": "Conditions for Australia",
                    "refusal_reasons": "",
                },
                [{"type": ["This field is required."]}],
            ),
            (
                {
                    "type": enums.RecommendationType.APPROVE,
                    "refusal_reasons": "",
                },
                [{"conditions": ["This field is required."]}],
            ),
            (
                {
                    "type": enums.RecommendationType.APPROVE,
                    "conditions": "No concerns",
                },
                [{"refusal_reasons": ["This field is required."]}],
            ),
            (
                {
                    "type": enums.RecommendationType.APPROVE,
                    "conditions": "No concerns",
                    "refusal_reasons": "",
                    "security_release_request": "138d3a5f-5b5d-457d-8db0-723e14b36de4",  # /PS-IGNORE
                },
                [
                    {
                        "security_release_request": [
                            'Invalid pk "138d3a5f-5b5d-457d-8db0-723e14b36de4" - object does not exist.'  # /PS-IGNORE
                        ]
                    }
                ],
            ),
        ),
    )
    def test_POST_recommendation_validation_errors(
        self, get_hawk_client, get_f680_application, url, team_case_advisor_headers, data, errors
    ):
        f680_application = get_f680_application()

        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        release_request = f680_application.security_release_requests.first()
        data = {"security_release_request": str(release_request.id), **data}
        api_client, target_url = get_hawk_client("POST", url(f680_application), data=[data])
        response = api_client.post(target_url, [data], **headers)
        assert response.status_code == 400
        assert response.json()["errors"] == errors

    def test_POST_recommendation_invalid_application_raises_error(self, get_hawk_client, team_case_advisor_headers):
        url = reverse(
            "caseworker_f680:recommendation", kwargs={"pk": "138d3a5f-5b5d-457d-8db0-723e14b36de4"}  # /PS-IGNORE
        )
        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        # Data is intentionally empty as we fail before validating the data
        api_client, target_url = get_hawk_client("POST", url, data=[])
        response = api_client.post(target_url, [], **headers)
        assert response.status_code == 404

    def test_DELETE_user_recommendation_success(self, get_hawk_client, get_f680_application, url, team_case_advisor):
        f680_application = get_f680_application()
        gov_user = team_case_advisor(TeamIdEnum.MOD_CAPPROT)

        for release_request in f680_application.security_release_requests.all():
            F680RecommendationFactory(
                case=f680_application,
                security_release_request=release_request,
                conditions="No concerns",
                user=gov_user,
                team=gov_user.team,
            )
        headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
        api_client, target_url = get_hawk_client("DELETE", url(f680_application))
        response = api_client.delete(target_url, **headers)
        assert response.status_code == 204
        assert f680_application.recommendations.count() == 0


class TestF680OutcomeViewSet:

    @freeze_time("2025-04-14 12:00:00")
    def test_GET_outcomes_exist(self, get_hawk_client, get_f680_application, team_case_advisor_headers):
        f680_application = get_f680_application()
        headers = team_case_advisor_headers(TeamIdEnum.MOD_ECJU)
        validity_start_date = timezone.now().date()
        validity_end_date = timezone.now().date() + relativedelta(
            months=+enums.SecurityReleaseOutcomeDuration.MONTHS_48
        )
        outcome = F680SecurityReleaseOutcomeFactory(
            case=f680_application,
            outcome=enums.SecurityReleaseOutcomes.APPROVE,
            security_grading=enums.SecurityGrading.OFFICIAL_SENSITIVE,
            conditions="No concerns",
            approval_types=["training"],
            validity_start_date=validity_start_date,
            validity_end_date=validity_end_date,
        )
        release_request_ids = [str(request.id) for request in f680_application.security_release_requests.all()]
        outcome.security_release_requests.set(release_request_ids)
        url = reverse("caseworker_f680:outcome", kwargs={"pk": str(f680_application.id)})
        api_client, target_url = get_hawk_client("GET", url, data=[])
        response = api_client.get(target_url, **headers)
        assert response.status_code == 200
        assert response.json() == [
            {
                "id": str(outcome.id),
                "case": str(f680_application.id),
                "approval_types": outcome.approval_types,
                "conditions": outcome.conditions,
                "outcome": outcome.outcome,
                "refusal_reasons": "",
                "security_grading": outcome.security_grading,
                "security_release_requests": release_request_ids,
                "team": str(outcome.team.id),
                "user": str(outcome.user.baseuser_ptr.id),
                "validity_start_date": validity_start_date.isoformat(),
                "validity_end_date": validity_end_date.isoformat(),
                "validity_period": 48,
            },
        ]

    def test_GET_outcomes_missing(self, get_hawk_client, get_f680_application, team_case_advisor_headers):
        f680_application = get_f680_application()
        headers = team_case_advisor_headers(TeamIdEnum.MOD_ECJU)
        url = reverse("caseworker_f680:outcome", kwargs={"pk": str(f680_application.id)})
        api_client, target_url = get_hawk_client("GET", url, data=[])
        response = api_client.get(target_url, **headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_GET_case_missing_404(self, get_hawk_client, team_case_advisor_headers):
        headers = team_case_advisor_headers(TeamIdEnum.MOD_ECJU)
        url = reverse("caseworker_f680:outcome", kwargs={"pk": uuid4()})
        api_client, target_url = get_hawk_client("GET", url, data=[])
        response = api_client.get(target_url, **headers)
        assert response.status_code == 404

    @freeze_time("2025-04-14 12:00:00")
    def test_POST_create_single_item_group_success(
        self, get_hawk_client, get_f680_application, team_case_advisor_headers
    ):
        f680_application = get_f680_application()
        f680_application.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        f680_application.save()
        headers = team_case_advisor_headers(TeamIdEnum.MOD_ECJU)
        url = reverse("caseworker_f680:outcome", kwargs={"pk": str(f680_application.id)})

        validity_start_date = timezone.now().date()
        validity_end_date = timezone.now().date() + relativedelta(
            months=+enums.SecurityReleaseOutcomeDuration.MONTHS_24
        )
        post_data = {
            "security_grading": "top-secret",
            "outcome": enums.SecurityReleaseOutcomes.APPROVE,
            "conditions": "my conditions",
            "approval_types": ["training"],
            "security_release_requests": [str(f680_application.security_release_requests.first().id)],
            "validity_start_date": validity_start_date.isoformat(),
            "validity_end_date": validity_end_date.isoformat(),
        }
        api_client, target_url = get_hawk_client("POST", url, data=post_data)
        response = api_client.post(target_url, post_data, **headers)
        assert response.status_code == 201

        outcome = SecurityReleaseOutcome.objects.first()
        assert outcome.security_grading == post_data["security_grading"]
        assert outcome.outcome == post_data["outcome"]
        assert outcome.conditions == post_data["conditions"]
        assert outcome.approval_types == post_data["approval_types"]
        release_request_ids = [str(request.id) for request in outcome.security_release_requests.all()]
        assert release_request_ids == post_data["security_release_requests"]
        assert outcome.refusal_reasons == ""
        assert str(outcome.team.id) == TeamIdEnum.MOD_ECJU
        assert outcome.validity_start_date == validity_start_date
        assert outcome.validity_end_date == validity_end_date

        assert response.json() == {
            "id": str(outcome.id),
            "case": str(f680_application.id),
            "approval_types": outcome.approval_types,
            "conditions": outcome.conditions,
            "outcome": outcome.outcome,
            "refusal_reasons": outcome.refusal_reasons,
            "security_grading": outcome.security_grading,
            "security_release_requests": release_request_ids,
            "team": str(outcome.team.id),
            "user": str(outcome.user.baseuser_ptr.id),
            "validity_start_date": validity_start_date.isoformat(),
            "validity_end_date": validity_end_date.isoformat(),
            "validity_period": 24,
        }

    @freeze_time("2025-04-14 12:00:00")
    def test_POST_create_multiple_item_group_success(
        self, get_hawk_client, get_f680_application, team_case_advisor_headers
    ):
        f680_application = get_f680_application()
        f680_application.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        f680_application.save()
        headers = team_case_advisor_headers(TeamIdEnum.MOD_ECJU)
        url = reverse("caseworker_f680:outcome", kwargs={"pk": str(f680_application.id)})
        release_request_ids = [str(request.id) for request in f680_application.security_release_requests.all()]
        post_data = {
            "outcome": enums.SecurityReleaseOutcomes.REFUSE,
            "refusal_reasons": "my reasons",
            "security_release_requests": release_request_ids,
        }
        api_client, target_url = get_hawk_client("POST", url, data=post_data)
        response = api_client.post(target_url, post_data, **headers)
        assert response.status_code == 201

        outcome = SecurityReleaseOutcome.objects.first()
        actual_release_request_ids = [str(request.id) for request in outcome.security_release_requests.all()]
        assert outcome.security_grading == None
        assert outcome.outcome == post_data["outcome"]
        assert outcome.refusal_reasons == post_data["refusal_reasons"]
        assert outcome.approval_types == []
        assert actual_release_request_ids == post_data["security_release_requests"]
        assert outcome.conditions == ""
        assert str(outcome.team.id) == TeamIdEnum.MOD_ECJU

        assert response.json() == {
            "id": str(outcome.id),
            "case": str(f680_application.id),
            "approval_types": outcome.approval_types,
            "conditions": outcome.conditions,
            "outcome": outcome.outcome,
            "refusal_reasons": outcome.refusal_reasons,
            "security_grading": outcome.security_grading,
            "security_release_requests": release_request_ids,
            "team": str(outcome.team.id),
            "user": str(outcome.user.baseuser_ptr.id),
            "validity_start_date": None,
            "validity_end_date": None,
            "validity_period": 0,
        }

    def test_POST_case_not_ready_for_outcome_permission_denied(
        self, get_hawk_client, get_f680_application, team_case_advisor_headers
    ):
        # case created in OGD advice status
        f680_application = get_f680_application()
        headers = team_case_advisor_headers(TeamIdEnum.MOD_ECJU)
        url = reverse("caseworker_f680:outcome", kwargs={"pk": str(f680_application.id)})
        release_request_ids = [str(request.id) for request in f680_application.security_release_requests.all()]
        post_data = {
            "outcome": enums.SecurityReleaseOutcomes.REFUSE,
            "refusal_reasons": "my reasons",
            "security_release_requests": release_request_ids,
        }
        api_client, target_url = get_hawk_client("POST", url, data=post_data)
        response = api_client.post(target_url, post_data, **headers)
        assert response.status_code == 403

    def test_POST_user_cannot_make_outcome_permission_denied(
        self, get_hawk_client, get_f680_application, team_case_advisor_headers
    ):
        # case created in OGD advice status
        f680_application = get_f680_application()
        f680_application.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        f680_application.save()
        # User in wrong team
        headers = team_case_advisor_headers(TeamIdEnum.MOD_CAPPROT)
        url = reverse("caseworker_f680:outcome", kwargs={"pk": str(f680_application.id)})
        release_request_ids = [str(request.id) for request in f680_application.security_release_requests.all()]
        post_data = {
            "outcome": enums.SecurityReleaseOutcomes.REFUSE,
            "refusal_reasons": "my reasons",
            "security_release_requests": release_request_ids,
        }
        api_client, target_url = get_hawk_client("POST", url, data=post_data)
        response = api_client.post(target_url, post_data, **headers)
        assert response.status_code == 403

    def test_POST_existing_outcome_responds_400(self, get_hawk_client, get_f680_application, team_case_advisor_headers):
        f680_application = get_f680_application()
        f680_application.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        f680_application.save()
        outcome = F680SecurityReleaseOutcomeFactory(
            case=f680_application,
            outcome=enums.SecurityReleaseOutcomes.APPROVE,
            security_grading=enums.SecurityGrading.OFFICIAL_SENSITIVE,
            conditions="No concerns",
            approval_types=["training"],
        )
        release_request_ids = [str(request.id) for request in f680_application.security_release_requests.all()]
        outcome.security_release_requests.set(release_request_ids)
        headers = team_case_advisor_headers(TeamIdEnum.MOD_ECJU)
        url = reverse("caseworker_f680:outcome", kwargs={"pk": str(f680_application.id)})
        post_data = {
            "outcome": enums.SecurityReleaseOutcomes.REFUSE,
            "refusal_reasons": "my reasons",
            "security_release_requests": release_request_ids,
        }
        api_client, target_url = get_hawk_client("POST", url, data=post_data)
        response = api_client.post(target_url, post_data, **headers)
        assert response.status_code == 400
        assert response.json() == {
            "errors": {
                "non_field_errors": [
                    "A SecurityReleaseOutcome record exists for one or more of the security release ids"
                ]
            }
        }

    @pytest.mark.parametrize(
        "data, expected_errors",
        (
            (
                {"invalid": "value"},
                {
                    "outcome": [
                        "This field is required.",
                    ],
                    "security_release_requests": [
                        "This field is required.",
                    ],
                },
            ),
            (
                {
                    "outcome": enums.SecurityReleaseOutcomes.REFUSE,
                    "security_release_requests": SECURITY_RELEASE_REQUEST_IDS,
                },
                {
                    "non_field_errors": [
                        "refusal_reasons required for refuse outcome",
                    ]
                },
            ),
            (
                {
                    "outcome": enums.SecurityReleaseOutcomes.REFUSE,
                    "refusal_reasons": "some reason",
                    "security_release_requests": SECURITY_RELEASE_REQUEST_IDS,
                    "approval_types": ["training"],
                },
                {
                    "non_field_errors": [
                        "approval_types invalid for refuse outcome",
                    ]
                },
            ),
            (
                {
                    "outcome": enums.SecurityReleaseOutcomes.REFUSE,
                    "refusal_reasons": "some reason",
                    "security_release_requests": SECURITY_RELEASE_REQUEST_IDS,
                    "security_grading": enums.SecurityGrading.OFFICIAL,
                },
                {
                    "non_field_errors": [
                        "security_grading invalid for refuse outcome",
                    ]
                },
            ),
            (
                {
                    "outcome": enums.SecurityReleaseOutcomes.REFUSE,
                    "refusal_reasons": "some reason",
                    "security_release_requests": SECURITY_RELEASE_REQUEST_IDS,
                    "conditions": "my condition",
                },
                {
                    "non_field_errors": [
                        "conditions invalid for refuse outcome",
                    ]
                },
            ),
            (
                {
                    "outcome": enums.SecurityReleaseOutcomes.APPROVE,
                    "security_release_requests": SECURITY_RELEASE_REQUEST_IDS,
                },
                {
                    "non_field_errors": [
                        "security_grading required for approve outcome",
                    ]
                },
            ),
            (
                {
                    "outcome": enums.SecurityReleaseOutcomes.APPROVE,
                    "security_release_requests": SECURITY_RELEASE_REQUEST_IDS,
                    "security_grading": enums.SecurityGrading.OFFICIAL,
                },
                {
                    "non_field_errors": [
                        "approval_types required for approve outcome",
                    ]
                },
            ),
            (
                {
                    "outcome": enums.SecurityReleaseOutcomes.APPROVE,
                    "security_release_requests": SECURITY_RELEASE_REQUEST_IDS,
                    "security_grading": enums.SecurityGrading.OFFICIAL,
                    "approval_types": ["training"],
                    "refusal_reasons": "some reasons",
                },
                {
                    "non_field_errors": [
                        "refusal_reasons invalid for approve outcome",
                    ]
                },
            ),
        ),
    )
    def test_POST_invalid_data(
        self, get_hawk_client, get_f680_application, url, team_case_advisor_headers, data, expected_errors
    ):
        f680_application = get_f680_application()
        f680_application.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        f680_application.save()
        headers = team_case_advisor_headers(TeamIdEnum.MOD_ECJU)
        url = reverse("caseworker_f680:outcome", kwargs={"pk": str(f680_application.id)})
        release_request_ids = [str(request.id) for request in f680_application.security_release_requests.all()]
        api_client, target_url = get_hawk_client("POST", url, data=data)
        response = api_client.post(target_url, data, **headers)
        assert response.status_code == 400
        assert response.json() == {"errors": expected_errors}

    def test_DELETE_success(self, get_hawk_client, get_f680_application, team_case_advisor_headers):
        f680_application = get_f680_application()
        f680_application.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        f680_application.save()
        headers = team_case_advisor_headers(TeamIdEnum.MOD_ECJU)
        release_request_ids = [str(request.id) for request in f680_application.security_release_requests.all()]
        outcome = F680SecurityReleaseOutcomeFactory(
            case_id=f680_application.id,
            outcome="refuse",
            refusal_reasons="my reasons",
        )
        outcome.security_release_requests.set(release_request_ids)
        url = reverse(
            "caseworker_f680:delete_outcome", kwargs={"pk": str(f680_application.id), "outcome_id": str(outcome.id)}
        )
        api_client, target_url = get_hawk_client("DELETE", url, data=[])
        response = api_client.delete(target_url, **headers)
        assert response.status_code == 204
        assert SecurityReleaseOutcome.objects.count() == 0

    def test_DELETE_case_missing_404(self, get_hawk_client, get_f680_application, team_case_advisor_headers):
        f680_application = get_f680_application()
        f680_application.status = CaseStatus.objects.get(status=CaseStatusEnum.UNDER_FINAL_REVIEW)
        f680_application.save()
        headers = team_case_advisor_headers(TeamIdEnum.MOD_ECJU)
        release_request_ids = [str(request.id) for request in f680_application.security_release_requests.all()]
        # Deliberately avoid linking the outcome with the case
        outcome = F680SecurityReleaseOutcomeFactory(
            outcome="refuse",
            refusal_reasons="my reasons",
        )
        outcome.security_release_requests.set(release_request_ids)
        url = reverse(
            "caseworker_f680:delete_outcome", kwargs={"pk": str(f680_application.id), "outcome_id": str(outcome.id)}
        )
        api_client, target_url = get_hawk_client("DELETE", url, data=[])
        response = api_client.delete(target_url, **headers)
        assert response.status_code == 404
        assert SecurityReleaseOutcome.objects.first() == outcome
