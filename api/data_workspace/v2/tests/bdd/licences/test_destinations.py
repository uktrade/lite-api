import pytest
from pytest_bdd import given, scenarios, then, when

from django.urls import reverse

from api.applications.models import PartyOnApplication
from api.licences.enums import LicenceStatus
from api.parties.enums import PartyType
from api.staticdata.statuses.enums import CaseStatusEnum

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
    application_id = party_on_application.application_id
    country_code = party_on_application.party.country.id
    party_type = party_on_application.party.type

    destination = {"application_id": str(application_id), "country_code": country_code, "type": party_type}
    assert destination in destinations


@given("a licence with deleted party is created", target_fixture="licence_with_deleted_party")
def licence_with_deleted_party_created(licence_with_deleted_party):
    assert licence_with_deleted_party.status == LicenceStatus.ISSUED
    application = licence_with_deleted_party.case.baseapplication
    assert PartyOnApplication.objects.filter(application=application).count() == 2


@then("the existing party is included in the extract")
def existing_party_included_in_extract(destinations):
    existing_party_on_application = PartyOnApplication.objects.get(deleted_at__isnull=True)
    application_id = existing_party_on_application.application_id
    country_code = existing_party_on_application.party.country.id
    party_type = existing_party_on_application.party.type

    assert PartyOnApplication.objects.filter(application_id=application_id).count() == 2

    destination = {"application_id": str(application_id), "country_code": country_code, "type": party_type}
    assert destination in destinations
    assert len(destinations) == 1


@then("the deleted party is not included in the extract")
def deleted_party_not_included_in_extract(destinations):
    deleted_party_on_application = PartyOnApplication.objects.get(deleted_at__isnull=False)
    application_id = deleted_party_on_application.application_id
    country_code = deleted_party_on_application.party.country.id
    party_type = deleted_party_on_application.party.type

    assert PartyOnApplication.objects.filter(application_id=application_id).count() == 2

    destination = {"application_id": str(application_id), "country_code": country_code, "type": party_type}
    assert destination not in destinations
    assert len(destinations) == 1


@given("a draft application is created")
def draft_application_created(draft_application):
    assert draft_application.status.status == CaseStatusEnum.DRAFT
    return draft_application


@then("the non-draft party is included in the extract")
def non_draft_party_is_included_in_extract(destinations):
    non_draft_party_on_application = PartyOnApplication.objects.get(
        application__status__status=CaseStatusEnum.FINALISED
    )
    application_id = non_draft_party_on_application.application_id
    country_code = non_draft_party_on_application.party.country.id
    party_type = non_draft_party_on_application.party.type

    destination = {"application_id": str(application_id), "country_code": country_code, "type": party_type}
    assert destination in destinations
    assert len(destinations) == 1


@then("draft parties are not included in the extract")
def draft_parties_not_included_in_extract(destinations):
    draft_parties_on_application = PartyOnApplication.objects.filter(application__status__status=CaseStatusEnum.DRAFT)

    application_id = draft_parties_on_application.first().application_id

    draft_end_user = draft_parties_on_application.get(party__type=PartyType.END_USER)
    draft_end_user_country_code = draft_end_user.party.country.id
    draft_end_user_party_type = draft_end_user.party.type

    assert PartyOnApplication.objects.filter(application_id=application_id).count() == 2

    draft_end_user_destination = {
        "application_id": str(application_id),
        "country_code": draft_end_user_country_code,
        "type": draft_end_user_party_type,
    }
    assert draft_end_user_destination not in destinations

    draft_consignee = draft_parties_on_application.get(party__type=PartyType.CONSIGNEE)
    draft_consignee_country_code = draft_consignee.party.country.id
    draft_consignee_party_type = draft_consignee.party.type

    draft_consignee_destination = {
        "application_id": str(application_id),
        "country_code": draft_consignee_country_code,
        "party_type": draft_consignee_party_type,
    }
    assert draft_consignee_destination not in destinations
    assert len(destinations) == 1
