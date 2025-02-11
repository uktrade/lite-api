import pytest


from api.audit_trail.enums import AuditType


@pytest.mark.django_db()
def test_populate_user_case_queue_movements(migrator):
    old_state = migrator.apply_initial_migration(("cases", "0080_casequeuemovement_user"))

    Audit = old_state.apps.get_model("audit_trail", "Audit")
    CaseQueueMovement = old_state.apps.get_model("cases", "CaseQueueMovement")
    Queue = old_state.apps.get_model("queues", "Queue")

    migrator.apply_tested_migration(("cases", "0081_populate_user_case_queue_movements"))

    move_case_qs = Audit.objects.filter(
        verb=AuditType.MOVE_CASE,
        action_object_object_id__isnull=False,
        payload__queues__isnull=False,
    )

    assert move_case_qs.count() == CaseQueueMovement.objects.count()

    for event in move_case_qs:
        case_id = event.action_object_object_id
        queue_name = event.payload["queues"]
        if Queue.objects.filter(name=queue_name).exists():
            queue = Queue.objects.get(name=queue_name)
            obj = CaseQueueMovement.objects.get(
                case_id=case_id,
                queue_id=queue.id,
                created_at=event.created_at,
            )

            assert event.actor == obj.actor
