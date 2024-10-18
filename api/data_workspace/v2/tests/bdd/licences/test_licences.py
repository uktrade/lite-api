import pytest

from django.urls import reverse
from pytest_bdd import (
    given,
    then,
    scenarios,
)

from api.licences.enums import LicenceStatus


scenarios("../scenarios/licences.feature")


@pytest.fixture()
def licences_list_url():
    return reverse("data_workspace:v2:dw-licences-list")


@given("a standard draft licence is created", target_fixture="draft_licence")
def standard_draft_licence_created(standard_draft_licence):
    assert standard_draft_licence.status == LicenceStatus.DRAFT
    return standard_draft_licence


@then("the draft licence is not included in the extract")
def draft_licence_not_included_in_extract(draft_licence, unpage_data, licences_list_url):
    licences = unpage_data(licences_list_url)

    assert draft_licence.reference_code not in [item["reference_code"] for item in licences]


@given("a standard licence is issued", target_fixture="issued_licence")
def standard_licence_issued(standard_licence):
    assert standard_licence.status == LicenceStatus.ISSUED
    return standard_licence


@then("the issued licence is included in the extract")
def licence_included_in_extract(issued_licence, unpage_data, licences_list_url):
    licences = unpage_data(licences_list_url)

    assert issued_licence.reference_code in [item["reference_code"] for item in licences]
