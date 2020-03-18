from cases.models import Case, CaseAssignment
from queues.models import Queue
from static.statuses.models import CaseStatus


def are_all_users_done_with_case_on_queue(case: Case, queue: Queue):
    return not CaseAssignment.objects.filter(case=case, queue=queue).exists()


def get_next_non_terminal_status(status: CaseStatus):
    # TODO Fix status ordering for automation
    next_priority = status.priority + 1
    try:
        return CaseStatus.objects.get(priority=next_priority, is_terminal=False)
    except CaseStatus.DoesNotExist:
        return None


def user_queue_assignment_workflow(queues: [Queue], case: Case):
    for queue in queues:
        if are_all_users_done_with_case_on_queue(case, queue):
            case.queues.remove(queue)

    if case.queues.count() == 0:
        next_status = get_next_non_terminal_status(case.status)
        if next_status:
            case.status = next_status
            case.save()
