import pytest
from pytest_bdd import given, scenarios, then, when

from django.urls import reverse

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
    assert False
