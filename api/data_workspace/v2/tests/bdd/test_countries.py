from django.urls import reverse
import pytest
from pytest_bdd import (
    then,
    when,
    scenarios,
)

scenarios("./scenarios/countries.feature")


@pytest.fixture()
def countries_list_url():
    return reverse("data_workspace:v2:dw-countries-list")


@when("I fetch the list of countries", target_fixture="countries")
def fetch_countries(countries_list_url, unpage_data):
    return unpage_data(countries_list_url)


@then("the correct country code and name is included in the extract")
def correct_country_code_included_in_extract(countries):
    example_country = {"code": "AE", "name": "United Arab Emirates"}
    assert example_country in countries


@then("the correct territory code and name is included in the extract")
def correct_territory_code_included_in_extract(countries):
    example_territory = {"code": "AE-DU", "name": "Dubai"}
    assert example_territory in countries
