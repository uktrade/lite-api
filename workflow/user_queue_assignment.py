from cases.models import Case, CaseAssignment
from queues.models import Queue
from static.statuses.models import CaseStatus


def are_all_users_done_with_case_on_queue(case: Case, queue: Queue):
    return not CaseAssignment.objects.filter(case=case, queue=queue).exists()


def move_case_to_next_non_terminal_status(case: Case):
    # TODO Fix status ordering for automation
    next_priority = case.status.priority + 1
    status = CaseStatus.objects.filter(priority=next_priority, is_terminal=False)
    if status:
        new_status = status.first()
        case.status = new_status
        case.save()


def user_queue_assignment_workflow(queues: [Queue], case: Case):
    for queue in queues:
        if are_all_users_done_with_case_on_queue(case, queue):
            case.queues.remove(queue)

    if case.queues.count() == 0:
        move_case_to_next_non_terminal_status(case)
