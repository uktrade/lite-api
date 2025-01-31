import pytest

from django.urls import reverse
from urllib import parse

from api.applications.tests.factories import DraftStandardApplicationFactory
from api.queues.constants import ALL_CASES_QUEUE_ID

pytest_plugins = [
    "api.tests.unit.fixtures.core",
]


@pytest.fixture
def cases_list(organisation, submit_application):

    applications = [DraftStandardApplicationFactory(organisation=organisation) for i in range(25)]
    cases = [submit_application(application) for application in applications]

    return cases


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
