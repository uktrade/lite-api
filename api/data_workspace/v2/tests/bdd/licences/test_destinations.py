from datetime import datetime
from pytest_bdd import scenarios, when


scenarios("../scenarios/destinations.feature")


@when("the parties are deleted")
def when_parties_are_deleted(issued_application):
    issued_application.parties.update(deleted_at=datetime.now())
