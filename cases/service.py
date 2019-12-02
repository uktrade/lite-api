from audit_trail import service as audit_trail_service
from audit_trail.constants import Verb
from cases.models import CaseAssignment


def update_case_queues(user, case, queues):
    update_queues = set([q.name for q in queues])
    initial_queues = set(case.queues.values_list("name", flat=True))
    remove_queues = initial_queues - update_queues
    new_queues = update_queues - initial_queues

    if remove_queues:
        CaseAssignment.objects.filter(queue__name__in=remove_queues).delete()

        audit_trail_service.create(
            actor=user,
            verb=Verb.REMOVED_QUEUES,
            target=case,
            payload={
                'queues': sorted(remove_queues)
            }
        )

    if new_queues:
        audit_trail_service.create(
            actor=user,
            verb=Verb.ADDED_QUEUES,
            target=case,
            payload={
                'queues': sorted(new_queues)
            }
        )
