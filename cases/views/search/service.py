from typing import List, Dict

from cases.enums import CaseType
from cases.views.search.queue import SearchQueue
from static.statuses.models import CaseStatus


def get_case_status_list() -> List[Dict]:
    return CaseStatus.objects.all().values('status', 'priority')


def get_case_type_list() -> List[Dict]:
    return CaseType.as_list()


def get_search_queues(team):
    return SearchQueue.all(team=team)
