from json import loads

from django.db.models import Q
from django.db.models.functions import Coalesce

from cases.models import Case
from conf.constants import SystemLimits
from conf.exceptions import NotFoundError
from conf.settings import ALL_CASES_SYSTEM_QUEUE_ID, OPEN_CASES_SYSTEM_QUEUE_ID
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status
from teams.models import Team


def _coalesce_case_status_priority(cases):
    case = cases.first()
    if case:
        case = case.__dict__
        if 'status__priority' not in case:
            return cases.annotate(
                status__priority=Coalesce('application__status__priority', 'clc_query__status__priority')
            )

    return cases


def sort_in_queryset(request, cases):
    sort = request.GET.get('sort', None)
    if sort:
        kwargs = []
        sort = loads(sort)
        if 'status' in sort:
            cases = _coalesce_case_status_priority(cases)
            order = '-' if sort['status'] == 'desc' else ''
            kwargs.append(order + 'status__priority')
            return cases.order_by(*kwargs)
    else:
        return cases


def sort_in_memory(request, cases):
    sort = request.GET.get('sort', None)
    if sort:
        sort = loads(sort)
        if 'status' in sort:
            if sort['status'] == 'desc':
                return sorted(cases, key=lambda k: k.status__priority)
            else:
                return sorted(cases, key=lambda k: k.status__priority).reverse
    else:
        return cases


def get_sorted_cases(request, queue_id, cases):
    if ALL_CASES_SYSTEM_QUEUE_ID == queue_id or OPEN_CASES_SYSTEM_QUEUE_ID == queue_id:
        return sort_in_memory(request, cases)
    else:
        return sort_in_queryset(request, cases)


def get_filtered_case_from_queryset(request, cases):
    kwargs = {}
    case_type = request.GET.get('case_type', None)
    if case_type:
        kwargs['type'] = case_type

    status = request.GET.get('status', None)
    if status:
        cases = _coalesce_case_status_priority(cases)
        priority = get_case_status_from_status(status).priority
        kwargs['status__priority'] = priority

    if kwargs:
        return cases.filter(**kwargs)
    else:
        return cases


def filter_in_memory(request, cases):
    case_type = request.GET.get('case_type', None)
    if case_type:
        cases = list(filter(lambda case: case.case_type.name == case_type, cases))

    status = request.GET.get('status', None)
    if status:
        priority = get_case_status_from_status(status).priority
        cases = list(filter(lambda case: case.status__priority == priority, cases))

    return cases


def get_filtered_cases(request, queue_id, cases):
    if ALL_CASES_SYSTEM_QUEUE_ID == queue_id or OPEN_CASES_SYSTEM_QUEUE_ID == queue_id:
        return filter_in_memory(request, cases)
    else:
        return get_filtered_case_from_queryset(request, cases)


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
        ).order_by('-created_at')[:SystemLimits.MAX_OPEN_CASES_RESULTS]

        return queue, cases
    else:
        return queue


def get_all_cases_queue(return_cases=False):
    queue = Queue(id=ALL_CASES_SYSTEM_QUEUE_ID,
                  name='All cases',
                  team=Team.objects.get(name='Admin'))

    if return_cases:
        # coalesce on status priority so that we can filter/sort later if needed
        cases = Case.objects.annotate(
            created_at=Coalesce('application__submitted_at', 'clc_query__submitted_at')
        ).order_by('-created_at')[:SystemLimits.MAX_ALL_CASES_RESULTS].annotate(
            status__priority=Coalesce('application__status__priority', 'clc_query__status__priority')
        )

        return queue, cases
    else:
        return queue


def get_queue(pk, return_cases=False):
    if ALL_CASES_SYSTEM_QUEUE_ID == str(pk):
        return get_all_cases_queue(return_cases)
    elif OPEN_CASES_SYSTEM_QUEUE_ID == str(pk):
        return get_open_cases_queue(return_cases)
    else:
        return get_non_system_queue(pk, return_cases)
