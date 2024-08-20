import pytest

from django.urls import reverse
from pytest_bdd import (
    given,
    parsers,
    then,
    scenarios,
)


scenarios("./scenarios/licence_statuses.feature")


@pytest.fixture()
def licence_status_list_url():
    return reverse("data_workspace:v2:dw-licence-statuses-list")


@given(
    parsers.parse("the following licence statuses:\n{licence_statuses}"), target_fixture="found_licence_status_names"
)
def the_following_licence_statuses(create_table, licence_statuses):
    licence_statuses = create_table(licence_statuses)
    return [licence_status["name"] for licence_status in licence_statuses]


@then("there are no other licence statuses")
def no_other_licence_statuses(found_licence_status_names, unpage_data, licence_status_list_url):
    licence_status_data = unpage_data(licence_status_list_url)
    assert sorted(found_licence_status_names) == sorted(
        [licence_status["name"] for licence_status in licence_status_data]
    )
