import pytest

from django.urls import reverse
from pytest_bdd import (
    given,
    scenarios,
    then,
)

from api.applications.tests.factories import (
    DraftStandardApplicationFactory,
    StandardApplicationFactory,
)


scenarios("./scenarios/siel_applications.feature")


@pytest.fixture()
def siel_applications_list_url():
    return reverse("data_workspace:v2:dw-siel-applications-list")


@given("a draft SIEL application", target_fixture="draft_siel_application")
def draft_siel_application():
    return DraftStandardApplicationFactory()


@then("it is not presented")
def draft_application_not_presented(unpage_data, siel_applications_list_url):
    siel_application_data = unpage_data(siel_applications_list_url)
    assert siel_application_data == []


@given("a submitted SIEL application without an amendment", target_fixture="siel_application")
def siel_application_without_an_amendment():
    return StandardApplicationFactory()


@then("it is presented as a single SIEL application", target_fixture="siel_application_data")
def presented_as_a_single_siel_application(client, siel_applications_list_url, unpage_data):
    siel_application_data = unpage_data(siel_applications_list_url)
    assert len(siel_application_data) == 1
    return siel_application_data


@then("the SIEL application has the id of itself")
def siel_application_id_of_itself(siel_application, siel_application_data):
    assert siel_application.pk == siel_application_data[0]["id"]


@given("a submitted SIEL application that has been amended", target_fixture="original_siel_application")
def siel_application_with_an_amendment():
    original_siel_application = StandardApplicationFactory()
    StandardApplicationFactory(amendment_of=original_siel_application)
    return original_siel_application


@then("the SIEL application has the id of the first SIEL application in the amendment chain")
def siel_application_has_first_id_in_amendment_chain(original_siel_application, siel_application_data):
    assert original_siel_application.pk == siel_application_data[0]["id"]


@given("a submitted SIEL application with multiple amendments", target_fixture="original_siel_application")
def siel_application_with_multiple_amendments():
    original_siel_application = StandardApplicationFactory()
    next_siel_application = StandardApplicationFactory(amendment_of=original_siel_application)
    another_siel_application = StandardApplicationFactory(amendment_of=next_siel_application)
    StandardApplicationFactory(amendment_of=another_siel_application)
    return original_siel_application
