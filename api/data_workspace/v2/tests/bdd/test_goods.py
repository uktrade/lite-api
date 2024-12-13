import pytest
from django.urls import reverse
from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

from api.applications.models import GoodOnApplication
from api.staticdata.statuses.enums import CaseStatusEnum

scenarios("./scenarios/goods.feature")


@pytest.fixture()
def goods_list_url():
    return reverse("data_workspace:v2:dw-goods-list")


@given("a standard application is created")
def standard_application_is_created(standard_application):
    assert standard_application.status.status in CaseStatusEnum.caseworker_operable_statuses()
    return standard_application


@when("I fetch all goods", target_fixture="goods")
def fetch_goods(goods_list_url, unpage_data):
    return unpage_data(goods_list_url)


@then("the quantity, unit, value are included in the extract")
def quantity_unit_value_are_included_in_extract(goods):
    good_on_application = GoodOnApplication.objects.get()
    quantity = good_on_application.quantity
    unit = good_on_application.unit
    value = good_on_application.value

    good = {
        "id": str(good_on_application.id),
        "application_id": str(good_on_application.application_id),
        "quantity": quantity,
        "unit": unit,
        "value": str(value),
    }
    assert good in goods


@given("a draft application is created")
def draft_application_is_created(draft_application):
    assert draft_application.status.status == CaseStatusEnum.DRAFT
    return draft_application


@then("the non-draft good is included in the extract")
def non_draft_good_is_included_in_extract(goods):
    good_on_application = (
        GoodOnApplication.objects.all().exclude(application__status__status=CaseStatusEnum.DRAFT).get()
    )
    quantity = good_on_application.quantity
    unit = good_on_application.unit
    value = good_on_application.value

    assert GoodOnApplication.objects.count() == 2

    good = {
        "id": str(good_on_application.id),
        "application_id": str(good_on_application.application_id),
        "quantity": quantity,
        "unit": unit,
        "value": str(value),
    }
    assert good in goods
    assert len(goods) == 1


@then("the draft good is not included in the extract")
def draft_good_is_not_included_in_extract(goods):
    draft_good_on_application = GoodOnApplication.objects.filter(application__status__status=CaseStatusEnum.DRAFT).get()
    quantity = draft_good_on_application.quantity
    unit = draft_good_on_application.unit
    value = draft_good_on_application.value

    assert GoodOnApplication.objects.count() == 2

    good = {
        "id": str(draft_good_on_application.id),
        "application_id": str(draft_good_on_application.application_id),
        "quantity": quantity,
        "unit": unit,
        "value": str(value),
    }
    assert good not in goods
    assert len(goods) == 1
