from pytest_bdd import (
    given,
    scenarios,
)
from api.licences.enums import LicenceStatus


scenarios("../scenarios/licence_decisions.feature")


@given("a standard draft licence is created", target_fixture="draft_licence")
def standard_draft_licence_created(standard_draft_licence):
    assert standard_draft_licence.status == LicenceStatus.DRAFT
    return standard_draft_licence


@given("a standard licence is cancelled", target_fixture="cancelled_licence")
def standard_licence_is_cancelled(standard_licence):
    standard_licence.status = LicenceStatus.CANCELLED
    standard_licence.save()

    return standard_licence
