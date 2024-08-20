import pytest

from django.urls import reverse
from pytest_bdd import (
    given,
    parsers,
    then,
    scenarios,
)
from rest_framework import status


scenarios("./scenarios/licence_statuses.feature")


def create_table(data_table):
    lines = data_table.strip().split("\n")

    keys = [key.strip() for key in lines[0].split("|") if key]

    parsed_data_table = []
    for line in lines[1:]:
        values = [value.strip() for value in line.split("|") if value]
        entry = dict(zip(keys, values))
        parsed_data_table.append(entry)

    return parsed_data_table


@pytest.fixture()
def unpage_data(client):
    def _unpage_data(url):
        unpaged_results = []
        while True:
            response = client.get(url)
            assert response.status_code == status.HTTP_200_OK
            unpaged_results += response.data["results"]
            if not response.data["next"]:
                break
            url = response.data["next"]

        return unpaged_results

    return _unpage_data


@pytest.fixture()
def licence_status_list_url():
    return reverse("data_workspace:v2:dw-licence-statuses-list")


@given(
    parsers.parse("the following licence statuses:\n{licence_statuses}"), target_fixture="found_licence_status_names"
)
def the_following_licence_statuses(licence_statuses):
    licence_statuses = create_table(licence_statuses)
    return [licence_status["name"] for licence_status in licence_statuses]


@then("there are no other licence statuses")
def no_other_licence_statuses(found_licence_status_names, unpage_data, licence_status_list_url):
    licence_status_data = unpage_data(licence_status_list_url)
    assert sorted(found_licence_status_names) == sorted(
        [licence_status["name"] for licence_status in licence_status_data]
    )
