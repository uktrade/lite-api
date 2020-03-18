from cases.models import Case, CaseAssignment
from queues.models import Queue
from static.statuses.models import CaseStatus


def get_queues_with_case_assignments(case: Case):
    return {assignment.queue for assignment in CaseAssignment.objects.filter(case=case).distinct("queue")}


def get_next_non_terminal_status(status: CaseStatus):
    # TODO Fix status ordering for automation
    next_priority = status.priority + 1
    try:
        return CaseStatus.objects.get(priority=next_priority, is_terminal=False)
    except CaseStatus.DoesNotExist:
        return None


def user_queue_assignment_workflow(queues: [Queue], case: Case):
    # Remove case from queues where all gov users are done with the case
    queues_without_case_assignments = set(queues) - get_queues_with_case_assignments(case)
    case.queues.remove(*queues_without_case_assignments)

    # Move case to next non-terminal state if unassigned from all queues
    if case.queues.count() == 0:
        next_status = get_next_non_terminal_status(case.status)
        if next_status:
            case.status = next_status
            case.save()
