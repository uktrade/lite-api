from pytest_bdd import given, parsers, scenarios, when

from api.applications.tests.factories import GoodOnApplicationFactory
from api.licences.tests.factories import StandardLicenceFactory
from api.licences.enums import LicenceStatus

scenarios("./scenarios/goods_on_licences.feature")


@given(parsers.parse("a standard application with the following goods:{goods}"), target_fixture="standard_application")
def standard_application_with_following_goods(parse_table, goods, standard_application):
    standard_application.goods.all().delete()
    good_attributes = parse_table(goods)[1:]
    for id, name in good_attributes:
        GoodOnApplicationFactory(
            application=standard_application,
            id=id,
            good__name=name,
        )
    return standard_application


@given(parsers.parse("a draft licence with attributes:{attributes}"), target_fixture="draft_licence")
def draft_licence_with_attributes(parse_attributes, attributes, standard_application):
    draft_licence = StandardLicenceFactory(
        case=standard_application, status=LicenceStatus.DRAFT, **parse_attributes(attributes)
    )
    return draft_licence


@when("the licence is issued")
def licence_is_issued(standard_application, issue_licence):
    issue_licence(standard_application)
    issued_application = standard_application.refresh_from_db()
    return issued_application
