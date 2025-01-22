import pytest

from django_test_migrations.migrator import Migrator

from api.staticdata.denial_reasons.constants import DENIAL_REASON_ID_TO_UUID_MAP


@pytest.mark.django_db()
def test_populate_uuid_field():
    migrator = Migrator(database="default")

    old_state = migrator.apply_initial_migration(("denial_reasons", "0006_populate_uuid_field"))
    DenialReason = old_state.apps.get_model("denial_reasons", "DenialReason")
    denial_reason = DenialReason.objects.get(id=1)
    assert (
        denial_reason.description
        == """Respect for the UK's international obligations and commitments, in particular sanctions adopted by the UN Security Council, agreements on non-proliferation and other subjects, as well as other international obligations.

Military End Use Control."""
    )

    new_state = migrator.apply_tested_migration(("denial_reasons", "0007_criterion_1_description_update"))
    DenialReason = new_state.apps.get_model("denial_reasons", "DenialReason")
    denial_reason = DenialReason.objects.get(id=1)
    assert (
        denial_reason.description
        == "Respect for the UK's international obligations and commitments, in particular sanctions adopted by the UN Security Council, agreements on non-proliferation and other subjects, as well as other international obligations."
    )

    expected_uuids = set(DENIAL_REASON_ID_TO_UUID_MAP.values())
    actual_uuids = set([str(denial_reason.uuid) for denial_reason in DenialReason.objects.all()])
    assert expected_uuids == actual_uuids
