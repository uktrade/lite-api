import pytest

from django.urls import reverse
from pytest_bdd import (
    given,
    parsers,
    then,
    scenarios,
)
from rest_framework import status


def create_table(data_table):
    lines = data_table.strip().split("\n")

    keys = [key.strip() for key in lines[0].split("|") if key]

    parsed_data_table = []
    for line in lines[1:]:
        values = [value.strip() for value in line.split("|") if value]
        entry = dict(zip(keys, values))
        parsed_data_table.append(entry)

    return parsed_data_table


scenarios("./scenarios/statuses.feature")


@pytest.fixture()
def status_list_url():
    return reverse("data_workspace:dw-statuses-list")


@given(parsers.parse("there is a status called {status_name}"), target_fixture="found_status")
def is_a_status_called(status_name, client, status_list_url):
    response = client.get(status_list_url)

    assert response.status_code == status.HTTP_200_OK
    for status_data in response.data:
        if status_data["name"] == status_name:
            return status_data

    pytest.fail(f"{status_name} not found")


@then(parsers.parse("it is marked as is_terminal {is_terminal}"))
def is_terminal(is_terminal, found_status):
    assert is_terminal == ("True" if found_status["is_terminal"] else "False")


@then(parsers.parse("it is marked as is_closed {is_closed}"))
def is_closed(is_closed, found_status):
    assert is_closed == ("True" if found_status["is_closed"] else "False")


@given(parsers.parse("the following statuses:\n{statuses}"), target_fixture="found_status_names")
def the_following_statuses(statuses):
    statuses = create_table(statuses)
    return [status["name"] for status in statuses]


@then("there are no other statuses")
def no_other_statuses(found_status_names, client, status_list_url):
    response = client.get(status_list_url)
    assert response.status_code == status.HTTP_200_OK
    assert sorted(found_status_names) == sorted([status["name"] for status in response.data])
