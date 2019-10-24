from typing import Dict

from django.db.models import Q
from django.db.models.functions import Coalesce
from django.http import Http404

from conf.exceptions import NotFoundError
from queues.constants import MY_TEAMS_QUEUES_CASES_ID, ALL_CASES_SYSTEM_QUEUE_ID, OPEN_CASES_SYSTEM_QUEUE_ID
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from teams.models import Team


def _coalesce_case_status_priority(cases):
    if cases.count():
        case = cases.first()
        case = case.__dict__
        if 'status__priority' not in case:
            return cases.annotate(
                status__priority=Coalesce('application__status__priority', 'query__status__priority')
            )

    return cases


def _all_cases_queue():
    queue = Queue(id=ALL_CASES_SYSTEM_QUEUE_ID,
                  name='All cases',
                  team=Team.objects.get(name='Admin'))
    queue.is_system_queue = True
    queue.query = Q()
    queue.reverse_ordering = True

    return queue


def _open_cases_queue():
    queue = Queue(id=OPEN_CASES_SYSTEM_QUEUE_ID,
                  name='Open cases',
                  team=Team.objects.get(name='Admin'))
    queue.is_system_queue = True
    queue.query = (~Q(application__status__status=CaseStatusEnum.WITHDRAWN) &
                   ~Q(application__status__status=CaseStatusEnum.FINALISED) &
                   ~Q(query__status__status=CaseStatusEnum.WITHDRAWN) &
                   ~Q(query__status__status=CaseStatusEnum.FINALISED))

    return queue


def _all_my_team_cases_queue(team):
    queue = Queue(id=MY_TEAMS_QUEUES_CASES_ID,
                  name='All my queues',
                  team=team)
    queue.is_system_queue = True
    my_team_queues = Queue.objects.filter(team=team)
    queue.query = Q(queues__in=my_team_queues)

    return queue


def get_queues(team: Team, include_system_queues=False):
    """
    Returns all queues
    Optionally returns system queues
    """
    queues = Queue.objects.all()

    if include_system_queues:
        queues = list(queues)
        queues.insert(0, _all_cases_queue())
        queues.insert(1, _open_cases_queue())
        queues.insert(2, _all_my_team_cases_queue(team))

    return queues


def get_queue(pk, team=None):
    """
    Returns the specified queue
    """
    queues = get_queues(team, True)
    queue = [queue for queue in queues if str(queue.id) == str(pk)]

    if queue:
        return queue[0]
    else:
        raise NotFoundError({'queue': 'Queue not found - ' + str(pk)})


def filter_cases(cases, filter_by: Dict[str, str]):
    """
    Given a list of cases, filter by filter parameter
    """
    kwargs = {}
    case_type = filter_by.get('case_type', None)
    if case_type:
        kwargs['type'] = case_type

    status = filter_by.get('status', None)
    if status:
        cases = _coalesce_case_status_priority(cases)
        priority = get_case_status_by_status(status).priority
        kwargs['status__priority'] = priority

    if kwargs:
        return cases.filter(**kwargs)

    return cases.all()


def sort_cases(cases, sort_by: str):
    """
    Given a list of cases, sort by the sort parameter
    Currently only supports: status
    """
    if sort_by:
        order = '-' if '-' in sort_by else ''
        if sort_by == 'status' or sort_by == '-status':
            cases = _coalesce_case_status_priority(cases)
            return cases.order_by(order + 'status__priority')
        else:
            raise Http404

    return cases.all()
