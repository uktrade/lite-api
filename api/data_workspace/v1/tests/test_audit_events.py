import pytest

from django.urls import reverse
from freezegun import freeze_time

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.users.libraries.user_to_token import user_to_token

from lite_routing.routing_rules_internal.enums import QueuesEnum, TeamIdEnum


pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


@pytest.fixture
def get_cases_on_ogd_queue(get_draft_application, submit_application):

    def _get_cases_on_ogd_queue(num_cases):
        applications = [get_draft_application() for _ in range(num_cases)]
        cases = [submit_application(application) for application in applications]

        for case in cases:
            case.status = get_case_status_by_status(CaseStatusEnum.OGD_ADVICE)
            case.save()

        return cases

    return _get_cases_on_ogd_queue


def submit_bulk_approve_recommendation(api_client, cases, gov_user):
    data = {
        "cases": [str(case.id) for case in cases],
        "advice": {
            "text": "No concerns",
            "proviso": "",
            "note": "",
            "footnote_required": False,
            "footnote": "",
            "team": TeamIdEnum.MOD_CAPPROT,
        },
    }
    url = reverse("caseworker_queues:bulk_approval", kwargs={"pk": QueuesEnum.MOD_CAPPROT})
    headers = {"HTTP_GOV_USER_TOKEN": user_to_token(gov_user.baseuser_ptr)}
    response = api_client.post(url, data=data, **headers)
    assert response.status_code == 201


@freeze_time("2025-01-10 12:00:00")
def test_audit_event_bulk_approval_recommendation(api_client, get_cases_on_ogd_queue, mod_officer):
    cases = get_cases_on_ogd_queue(4)

    submit_bulk_approve_recommendation(api_client, cases, mod_officer)

    expected_fields = ("id", "created_at", "user", "case", "queue")

    url = reverse("data_workspace:v1:dw-audit-bulk-approval-list")
    response = api_client.get(url)

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 4
    assert tuple(results[0].keys()) == expected_fields

    for item in results:
        item.pop("id")

    assert results == [
        {
            "created_at": "2025-01-10T12:00:00Z",
            "user": str(mod_officer.baseuser_ptr.id),
            "case": str(case.id),
            "queue": "mod-capprot cases to review",
        }
        for case in cases
    ]


@freeze_time("2025-01-10 12:00:00")
def test_audit_event_bulk_approval_recommendation_options_method(api_client, get_cases_on_ogd_queue, mod_officer):
    cases = get_cases_on_ogd_queue(4)

    submit_bulk_approve_recommendation(api_client, cases, mod_officer)

    url = reverse("data_workspace:v1:dw-audit-bulk-approval-list")
    response = api_client.options(url)

    assert response.status_code == 200
    options = response.json()["actions"]["GET"]
    assert options == {
        "id": {"type": "string", "required": False, "read_only": True, "label": "Id"},
        "created_at": {"type": "datetime", "required": False, "read_only": True, "label": "Created_at"},
        "user": {"type": "field", "required": False, "read_only": True, "label": "User"},
        "case": {"type": "field", "required": False, "read_only": True, "label": "Case"},
        "queue": {"type": "field", "required": False, "read_only": True, "label": "Queue"},
    }
