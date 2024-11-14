import pytest

from api.cases.enums import LicenceDecisionType

INITIAL_MIGRATION = "0068_populate_licence_decisions"
MIGRATION_UNDER_TEST = "0069_attach_licence_to_licence_decision"


@pytest.mark.django_db()
def test_attach_licence_to_licence_decisions(migrator):

    old_state = migrator.apply_initial_migration(("cases", INITIAL_MIGRATION))
    new_state = migrator.apply_tested_migration(("cases", MIGRATION_UNDER_TEST))

    LicenceDecision = new_state.apps.get_model("cases", "LicenceDecision")

    assert all(
        item.licence == item.case.licences.earliest("created_at")
        for item in LicenceDecision.objects.filter(decision=LicenceDecisionType.ISSUED)
    )
