from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.models import CaseAssignment


def update_case_queues(user, case, queues):
    """
    Update the queues a Case is on and create an audit trail.
    """
    update_queues = set([q.name for q in queues])
    initial_queues = set(case.queues.values_list("name", flat=True))
    removed_queues = initial_queues - update_queues
    new_queues = update_queues - initial_queues
    if removed_queues:
        CaseAssignment.objects.filter(queue__name__in=removed_queues).delete()
        audit_trail_service.create(
            actor=user,
            verb=AuditType.REMOVE_CASE,
            target=case,
            payload={
                'queues': sorted(removed_queues)
            }
        )

    if new_queues:
        audit_trail_service.create(
            actor=user,
            verb=AuditType.MOVE_CASE,
            target=case,
            payload={
                'queues': sorted(new_queues)
            }
        )
