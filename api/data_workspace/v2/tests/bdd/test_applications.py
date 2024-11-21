from pytest_bdd import (
    given,
    scenarios,
)

from api.applications.tests.factories import DraftStandardApplicationFactory


scenarios("./scenarios/applications.feature")


@given("a draft standard application")
def draft_standard_application():
    DraftStandardApplicationFactory()
