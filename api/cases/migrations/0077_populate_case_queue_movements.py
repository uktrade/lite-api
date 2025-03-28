# Generated by Django 4.2.16 on 2025-02-03 11:33

from django.db import migrations, transaction


from api.audit_trail.enums import AuditType


@transaction.atomic
def populate_case_queue_movements(apps, schema_editor):
    Audit = apps.get_model("audit_trail", "Audit")
    CaseQueueMovement = apps.get_model("cases", "CaseQueueMovement")
    Queue = apps.get_model("queues", "Queue")

    case_queue_movements = []

    move_case_qs = Audit.objects.filter(
        verb=AuditType.MOVE_CASE,
        action_object_object_id__isnull=False,
        payload__queue_ids__isnull=False,
        payload__queues__isnull=False,
    )
    for event in move_case_qs:
        case_id = event.action_object_object_id

        for queue_id in event.payload["queue_ids"]:
            case_queue_movements.append(
                CaseQueueMovement(
                    case_id=case_id,
                    queue_id=queue_id,
                    created_at=event.created_at,
                )
            )

    # Some of the early events only have queue name in the payload so they are processed separately
    move_case_qs = Audit.objects.filter(
        verb=AuditType.MOVE_CASE,
        action_object_object_id__isnull=False,
        payload__queue_ids__isnull=True,
        payload__queues__isnull=False,
    )
    for event in move_case_qs:
        case_id = event.action_object_object_id
        queue_name = event.payload["queues"]
        if Queue.objects.filter(name=queue_name).exists():
            queue = Queue.objects.get(name=queue_name)

            case_queue_movements.append(
                CaseQueueMovement(
                    case_id=case_id,
                    queue_id=queue.id,
                    created_at=event.created_at,
                )
            )

    CaseQueueMovement.objects.bulk_create(case_queue_movements)


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0076_casequeuemovement"),
    ]

    operations = [
        migrations.RunPython(
            populate_case_queue_movements,
            migrations.RunPython.noop,
        ),
    ]
