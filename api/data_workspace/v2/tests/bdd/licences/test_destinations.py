import pytest
from pytest_bdd import given, scenarios, then, when

from django.urls import reverse

from api.applications.models import PartyOnApplication
from api.licences.enums import LicenceStatus

scenarios("../scenarios/destinations.feature")


@pytest.fixture()
def destinations_list_url():
    return reverse("data_workspace:v2:dw-destinations-list")


@given("a standard licence is created", target_fixture="licence")
def standard_licence_created(standard_licence):
    assert standard_licence.status == LicenceStatus.ISSUED
    return standard_licence


@when("I fetch all destinations", target_fixture="destinations")
def fetch_all_destinations(destinations_list_url, unpage_data):
    return unpage_data(destinations_list_url)


@then("the country code and type are included in the extract")
def country_code_and_type_included_in_extract(destinations):
    party_on_application = PartyOnApplication.objects.get()
    application_id = party_on_application.application.id
    country_code = party_on_application.party.country.id
    party_type = party_on_application.party.type

    destination = {"application_id": application_id, "country_code": country_code, "type": party_type}
    assert destination in destinations
