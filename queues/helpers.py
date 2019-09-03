from typing import Dict

from django.db.models import Q
from django.db.models.functions import Coalesce
from django.http import Http404

from cases.models import Case
from conf.exceptions import NotFoundError
from queues.constants import ALL_MY_QUEUES_ID, ALL_CASES_SYSTEM_QUEUE_ID, OPEN_CASES_SYSTEM_QUEUE_ID
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status
from teams.models import Team


def _coalesce_case_status_priority(cases):
    if len(cases):
        case = cases[0]
        case = case.__dict__
        if 'status__priority' not in case:
            return cases.annotate(
                status__priority=Coalesce('application__status__priority', 'clc_query__status__priority')
            )

    return cases


def get_non_system_queue(pk, return_cases=False):
    try:
        if return_cases:
            # get the cases separately so they can be sorted and re-assigned to the queue queryset object
            queue = Queue.objects.defer('cases').get(pk=pk)
            cases = Case.objects.filter(queues=queue)
            return queue, cases
        else:
            return Queue.objects.get(pk=pk)
    except Queue.DoesNotExist:
        raise NotFoundError({'queue': 'Queue not found'})


def get_open_cases_queue(return_cases=False):
    queue = Queue(id=OPEN_CASES_SYSTEM_QUEUE_ID,
                  name='Open cases',
                  team=Team.objects.get(name='Admin'))
    queue.is_system_queue = True
    cases = Case.objects.annotate(
        status__priority=Coalesce('application__status__priority', 'clc_query__status__priority')
    )

    queue.cases_count = cases.filter(~Q(status__priority=CaseStatusEnum.priorities[CaseStatusEnum.WITHDRAWN]) &
                                     ~Q(status__priority=CaseStatusEnum.priorities[CaseStatusEnum.DECLINED]) &
                                     ~Q(status__priority=CaseStatusEnum.priorities[CaseStatusEnum.APPROVED])).count()

    if return_cases:
        # coalesce on status priority so that we can filter/sort later if needed
        cases = Case.objects.annotate(
            created_at=Coalesce('application__submitted_at', 'clc_query__submitted_at'),
            status__priority=Coalesce('application__status__priority', 'clc_query__status__priority')
        )

        cases = cases.filter(
            ~Q(status__priority=CaseStatusEnum.priorities[CaseStatusEnum.WITHDRAWN]) &
            ~Q(status__priority=CaseStatusEnum.priorities[CaseStatusEnum.DECLINED]) &
            ~Q(status__priority=CaseStatusEnum.priorities[CaseStatusEnum.APPROVED])
        ).order_by('-created_at')

        return queue, cases
    else:
        return queue


def get_all_cases_queue(return_cases=False):
    queue = Queue(id=ALL_CASES_SYSTEM_QUEUE_ID,
                  name='All cases',
                  team=Team.objects.get(name='Admin'))
    queue.is_system_queue = True
    queue.cases_count = Case.objects.count()

    if return_cases:
        # coalesce on status priority so that we can filter/sort later if needed
        cases = Case.objects.all()
        return queue, cases
    else:
        return queue


def get_all_my_team_cases_queue(team, return_cases=False):
    queue = Queue(id=ALL_MY_QUEUES_ID,
                  name='All my queues',
                  team=team)
    queue.is_system_queue = True
    my_team_queues = Queue.objects.filter(team=team)
    cases = Case.objects.filter(queues__in=my_team_queues).distinct()
    queue.cases_count = cases.count()

    if return_cases:
        return queue, cases
    else:
        return queue


def get_queue(pk, team=None, return_cases=False):
    if ALL_CASES_SYSTEM_QUEUE_ID == str(pk):
        return get_all_cases_queue(return_cases)
    elif OPEN_CASES_SYSTEM_QUEUE_ID == str(pk):
        return get_open_cases_queue(return_cases)
    elif ALL_MY_QUEUES_ID == str(pk):
        return get_all_my_team_cases_queue(return_cases=return_cases, team=team)
    else:
        return get_non_system_queue(pk, return_cases)


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
        priority = get_case_status_from_status(status).priority
        kwargs['status__priority'] = priority

    if kwargs:
        return cases.filter(**kwargs)
    else:
        return cases


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

    return cases


def get_queue_cases(queue_pk, team=None):
    if ALL_CASES_SYSTEM_QUEUE_ID == str(queue_pk):
        queue, cases = get_all_cases_queue(True)
    elif OPEN_CASES_SYSTEM_QUEUE_ID == str(queue_pk):
        queue, cases = get_open_cases_queue(True)
    elif ALL_MY_QUEUES_ID == str(queue_pk):
        queue, cases = get_all_my_team_cases_queue(return_cases=True, team=team)
    else:
        queue, cases = get_non_system_queue(queue_pk, True)

    return cases
