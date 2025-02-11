import pytest

from freezegun import freeze_time

from django.urls import reverse
from urllib import parse

from api.applications.tests.factories import DraftStandardApplicationFactory
from api.core.constants import Roles
from api.queues.constants import ALL_CASES_QUEUE_ID
from api.teams.models import Team
from api.users.enums import UserType
from api.users.libraries.user_to_token import user_to_token
from api.users.models import Role
from api.users.tests.factories import GovUserFactory, RoleFactory

from lite_routing.routing_rules_internal.enums import QueuesEnum, TeamIdEnum

pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


@pytest.fixture()
def team_case_advisor():
    def _team_case_advisor(team_id):
        gov_user = GovUserFactory()
        if not Role.objects.filter(id=Roles.INTERNAL_DEFAULT_ROLE_ID, type=UserType.INTERNAL.value).exists():
            gov_user.role = RoleFactory(
                id=Roles.INTERNAL_DEFAULT_ROLE_ID, type=UserType.INTERNAL.value, name=Roles.INTERNAL_DEFAULT_ROLE_NAME
            )
        gov_user.team = Team.objects.get(id=team_id)
        gov_user.save()
        return gov_user

    return _team_case_advisor


@pytest.fixture()
def team_case_advisor_headers(team_case_advisor):
    def _team_case_advisor_headers(team_id):
        case_advisor = team_case_advisor(team_id)
        return {"HTTP_GOV_USER_TOKEN": user_to_token(case_advisor.baseuser_ptr)}

    return _team_case_advisor_headers


@pytest.fixture
def cases_list(organisation, submit_application):

    applications = [DraftStandardApplicationFactory(organisation=organisation) for i in range(25)]
    cases = [submit_application(application) for application in applications]

    return cases


@pytest.fixture
def get_cases_with_queue_movements(api_client, cases_list, team_case_advisor_headers):

    def _get_cases_with_queue_movements():
        cases = []

        # Move even index cases first followed by odd index to create randomness
        indexes = list(range(0, len(cases_list), 2)) + list(range(1, len(cases_list), 2))
        for i, index in enumerate(indexes):
            case = cases_list[index]
            cases.append(case)

            action_time = f"2025-01-10T12:{i}:00+00:00"
            freezer = freeze_time(action_time)
            freezer.start()

            url = reverse("cases:assigned_queues", kwargs={"pk": case.id})
            headers = team_case_advisor_headers(TeamIdEnum.LICENSING_RECEPTION)
            response = api_client.put(
                url, data={"queues": [QueuesEnum.LICENSING_RECEPTION_SIEL_APPLICATIONS]}, **headers
            )
            assert response.status_code == 200
            freezer.stop()

        return cases

    return _get_cases_with_queue_movements


def test_cases_sorting_newest_first(api_client, gov_headers, cases_list):
    query_params = {"queue_id": ALL_CASES_QUEUE_ID, "sort_by": "-submitted_at"}
    url = f"{reverse('cases:search')}?{parse.urlencode(query_params, doseq=True)}"
    response = api_client.get(url, **gov_headers)
    assert response.status_code == 200
    response = response.json()["results"]

    assert len(response["cases"]) == len(cases_list)
    expected_case_order = [case.reference_code for case in reversed(cases_list)]
    actual_case_order = [case["reference_code"] for case in response["cases"]]
    assert actual_case_order == expected_case_order


def test_cases_sorting_oldest_first(api_client, gov_headers, cases_list):
    query_params = {"queue_id": ALL_CASES_QUEUE_ID, "sort_by": "submitted_at"}
    url = f"{reverse('cases:search')}?{parse.urlencode(query_params, doseq=True)}"
    response = api_client.get(url, **gov_headers)
    assert response.status_code == 200
    response = response.json()["results"]

    assert len(response["cases"]) == len(cases_list)
    expected_case_order = [case.reference_code for case in cases_list]
    actual_case_order = [case["reference_code"] for case in response["cases"]]
    assert actual_case_order == expected_case_order


# Tests for the time_on_queue sorting
# Initially we create a list of cases and moved forward from Licensing reception queue.
# This will assign those cases to TAU queue and create necessary CaseQueueMovement instances.
# To add randomness initially all even index cases are moved forward followed by odd index ones
# and the same order is asserted in the tests
def test_cases_sorting_time_on_queue_newest_first(api_client, gov_headers, get_cases_with_queue_movements):

    cases = get_cases_with_queue_movements()
    query_params = {"queue_id": QueuesEnum.TECHNICAL_ASSESSMENT_UNIT_SIELS_TO_REVIEW, "sort_by": "-time_on_queue"}
    url = f"{reverse('cases:search')}?{parse.urlencode(query_params, doseq=True)}"
    response = api_client.get(url, **gov_headers)
    assert response.status_code == 200
    response = response.json()["results"]

    assert len(response["cases"]) == len(cases)
    expected_case_order = [case.reference_code for case in reversed(cases)]
    actual_case_order = [case["reference_code"] for case in response["cases"]]
    assert actual_case_order == expected_case_order


def test_cases_sorting_time_on_queue_oldest_first(api_client, gov_headers, get_cases_with_queue_movements):

    cases = get_cases_with_queue_movements()
    query_params = {"queue_id": QueuesEnum.TECHNICAL_ASSESSMENT_UNIT_SIELS_TO_REVIEW, "sort_by": "time_on_queue"}
    url = f"{reverse('cases:search')}?{parse.urlencode(query_params, doseq=True)}"
    response = api_client.get(url, **gov_headers)
    assert response.status_code == 200
    response = response.json()["results"]

    assert len(response["cases"]) == len(cases)
    expected_case_order = [case.reference_code for case in cases]
    actual_case_order = [case["reference_code"] for case in response["cases"]]
    assert actual_case_order == expected_case_order
