import pytest

from django.urls import reverse
from pytest_bdd import (
    given,
    parsers,
    then,
    scenarios,
)


scenarios("./scenarios/licence_decision_types.feature")


@pytest.fixture()
def licence_decision_type_list_url():
    return reverse("data_workspace:v2:dw-licence-decision-types-list")


@given(
    parsers.parse("the following licence decision types:\n{licence_decision_types}"),
    target_fixture="found_licence_decision_type_names",
)
def the_following_licence_decision_types(create_table, licence_decision_types):
    licence_decision_types = create_table(licence_decision_types)
    return [licence_decision_type["name"] for licence_decision_type in licence_decision_types]


@then("there are no other licence decision types")
def no_other_licence_decision_types(found_licence_decision_type_names, unpage_data, licence_decision_type_list_url):
    licence_decision_type_data = unpage_data(licence_decision_type_list_url)
    assert sorted(found_licence_decision_type_names) == sorted(
        [licence_decision_type["name"] for licence_decision_type in licence_decision_type_data]
    )
