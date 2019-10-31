from typing import List, Dict

from cases.enums import CaseType
from cases.models import Case
from cases.views.search.queue import SearchQueue
from queues.constants import ALL_CASES_SYSTEM_QUEUE_ID, MY_TEAMS_QUEUES_CASES_ID, OPEN_CASES_SYSTEM_QUEUE_ID
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum


def get_search_queues(user) -> List[Queue]:
    """
    Retrieves meta information on all the queues available for a user.
    """
    return SearchQueue.system(team=user.team) + [SearchQueue.from_queue(queue) for queue in Queue.objects.all()]


def search_cases(queue_id=None, team=None, status=None, case_type=None, sort=None):
    """
    Search for a user's available cases given a set of search parameters.
    """
    case_qs = Case.objects.all()

    if queue_id == MY_TEAMS_QUEUES_CASES_ID:
        case_qs = case_qs.in_team(team=team)

    elif queue_id == OPEN_CASES_SYSTEM_QUEUE_ID:
        case_qs = case_qs.is_open()

    elif queue_id is not None and queue_id != ALL_CASES_SYSTEM_QUEUE_ID:
        case_qs = case_qs.in_queue(queue_id=queue_id)

    if status:
        case_qs = case_qs.has_status(status=status)

    if case_type:
        case_qs = case_qs.is_type(case_type=case_type)

    case_qs = case_qs.order_by_date()

    if isinstance(sort, str):
        case_qs = case_qs.order_by_status(order='-' if sort.startswith('-') else '')

    return case_qs


def get_case_status_list() -> List[Dict]:
    """Used by migration and views for consistency."""
    return [
        {
            'status': choice[0],
            'priority': CaseStatusEnum.priorities[choice[0]]
        } for choice in CaseStatusEnum.choices
    ]


def get_case_type_list() -> List[Dict]:
    return [
        {
            'value': choice[0],
            'title': choice[1],
        } for choice in CaseType.choices
    ]
