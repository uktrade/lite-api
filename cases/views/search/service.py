from typing import List, Dict

from cases.enums import CaseType
from cases.views.search.queue import SearchQueue
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum


def get_search_queues(user) -> List[Queue]:
    """
    Retrieves meta information on all the queues available for a user.
    """
    return SearchQueue.system(team=user.team) + [SearchQueue.from_queue(queue) for queue in Queue.objects.all()]


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
