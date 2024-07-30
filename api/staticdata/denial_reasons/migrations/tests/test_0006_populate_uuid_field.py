import pytest
import uuid

from django_test_migrations.migrator import Migrator


@pytest.mark.django_db()
def test_populate_uuid_field():
    migrator = Migrator(database="default")

    old_state = migrator.apply_initial_migration(("denial_reasons", "0005_denialreason_uuid"))

    new_state = migrator.apply_tested_migration(("denial_reasons", "0006_populate_uuid_field"))
    DenialReason = new_state.apps.get_model("denial_reasons", "DenialReason")
    for denial_reason in DenialReason.objects.all():
        assert denial_reason.uuid is not None
        assert type(denial_reason.uuid) is uuid.UUID

    # Assert there is a unique UUID for each DenialReason object
    assert DenialReason.objects.all().count() == len(
        set([denial_reason.uuid for denial_reason in DenialReason.objects.all()])
    )
