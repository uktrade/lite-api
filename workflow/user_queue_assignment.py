from cases.models import Case, CaseAssignment
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus


def get_queues_with_case_assignments(case: Case):
    return {assignment.queue for assignment in CaseAssignment.objects.filter(case=case).distinct("queue")}


def get_next_non_terminal_status(status: CaseStatus):
    """
    Gets the next non-terminal status from SUBMITTED to UNDER_FINAL_REVIEW
    SUBMITTED, APPLICANT_EDITING & RESUBMITTED will always return INITIAL_CHECKS
    returns the next status or None if status change is invalid
    """
    if (
        CaseStatusEnum.priority[CaseStatusEnum.DRAFT]
        < status.priority
        < CaseStatusEnum.priority[CaseStatusEnum.FINALISED]
    ):
        # All statuses from priority 1-3 (submitted, applicant_editing, resubmitted) are the same
        # and so the next status should be INITIAL_CHECKS
        if status.priority < 4:
            next_priority = CaseStatusEnum.priority[CaseStatusEnum.INITIAL_CHECKS]
        else:
            # All statuses from INITIAL_CHECKS onwards are just an increase of 1
            next_priority = status.priority + 1

        try:
            # Ensure new status is not terminal
            return CaseStatus.objects.get(priority=next_priority, is_terminal=False)
        except CaseStatus.DoesNotExist:
            return None
    else:
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
