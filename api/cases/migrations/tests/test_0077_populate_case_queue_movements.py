import pytest


from api.audit_trail.enums import AuditType


@pytest.mark.django_db()
def test_populate_case_queue_movements(migrator):
    old_state = migrator.apply_initial_migration(("cases", "0076_casequeuemovement"))

    Audit = old_state.apps.get_model("audit_trail", "Audit")
    CaseQueueMovement = old_state.apps.get_model("cases", "CaseQueueMovement")

    migrator.apply_tested_migration(("cases", "0077_populate_case_queue_movements"))

    move_case_qs = Audit.objects.filter(
        verb=AuditType.MOVE_CASE,
        action_object_object_id__isnull=False,
        payload__queues__isnull=False,
    )

    assert move_case_qs.count() == CaseQueueMovement.objects.count()
