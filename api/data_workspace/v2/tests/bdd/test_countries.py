from django.urls import reverse
import pytest
from pytest_bdd import (
    given,
    then,
    when,
    scenarios,
)

from api.staticdata.countries.models import Country

scenarios("./scenarios/countries.feature")


@pytest.fixture()
def countries_list_url():
    return reverse("data_workspace:v2:dw-countries-list")


@pytest.fixture()
def example_country():
    return {"id": "EX", "name": "Example", "is_eu": False}


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


@given("I add a new country to the countries list")
def add_new_country_to_countries_list(example_country):
    Country.objects.create(**example_country)


@then("the new country appears in the extract")
def new_country_appears_in_extract(countries, example_country):
    new_country = {"code": example_country["id"], "name": example_country["name"]}
    assert new_country in countries


@given("I remove the new country from the countries list")
def remove_new_country_from_countries_list(example_country):
    new_country = Country.objects.get(id=example_country["id"])
    new_country.delete()


@then("the new country does not appear in the extract")
def new_country_does_not_appear_in_extract(countries, example_country):
    new_country = {"code": example_country["id"], "name": example_country["name"]}
    assert new_country not in countries
