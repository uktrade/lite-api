from django.db.models import Q
from json import loads
from django.db.models.functions import Coalesce
from cases.models import Case
from conf.constants import SystemLimits
from conf.exceptions import NotFoundError
from conf.settings import ALL_CASES_SYSTEM_QUEUE_ID, OPEN_CASES_SYSTEM_QUEUE_ID
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus
from teams.models import Team


def _coalesce_cases(cases):
    # coalescing on status' priority so we can filter and order if needed
    return cases.annotate(
        status__priority=Coalesce('application__status__priority', 'clc_query__status__priority')
    )


def get_sorted_cases(request, cases):
    sort = request.GET.get('sort', None)
    if sort:
        kwargs = []
        sort = loads(sort)
        if 'status' in sort:
            order = '-' if sort['status'] == 'desc' else ''
            kwargs.append(order + 'status__priority')

        if kwargs:
            return cases.order_by(*kwargs)

    return cases.annotate(
        created_at=Coalesce('application__submitted_at', 'clc_query__submitted_at')
    ).order_by('-created_at')


def get_filtered_cases(request, cases):
    kwargs = {}
    case_type = request.GET.get('case_type', None)
    if case_type:
        kwargs['case_type__name'] = case_type

    status = request.GET.get('status', None)
    if status:
        status = CaseStatus.objects.get(status=status).priority
        kwargs['status__priority'] = status

    return cases.filter(**kwargs)


def get_all_cases_queue(with_cases=False):
    queue = Queue(id=ALL_CASES_SYSTEM_QUEUE_ID,
                  name='All cases',
                  team=Team.objects.get(name='Admin'))

    if with_cases:
        cases = _coalesce_cases(Case.objects.all())
        return queue, cases, SystemLimits.MAX_OPEN_CASES_RESULTS

    return queue


def get_open_cases_queue(with_cases=False):
    queue = Queue(id=OPEN_CASES_SYSTEM_QUEUE_ID,
                  name='Open cases',
                  team=Team.objects.get(name='Admin'))

    if with_cases:
        cases = _coalesce_cases(Case.objects.all())
        withdrawn_status_priority = CaseStatus.objects.get(status=CaseStatusEnum.WITHDRAWN).priority
        approved_status_priority = CaseStatus.objects.get(status=CaseStatusEnum.APPROVED).priority
        declined_status_priority = CaseStatus.objects.get(status=CaseStatusEnum.DECLINED).priority
        cases = cases.filter(
            ~Q(status__priority=withdrawn_status_priority) &
            ~Q(status__priority=approved_status_priority) &
            ~Q(status__priority=declined_status_priority)
        )
        return queue, cases, SystemLimits.MAX_OPEN_CASES_RESULTS

    return queue


def get_queue(pk, with_cases=False):
    if ALL_CASES_SYSTEM_QUEUE_ID == str(pk):
        return get_all_cases_queue(with_cases)
    elif OPEN_CASES_SYSTEM_QUEUE_ID == str(pk):
        return get_open_cases_queue(with_cases)
    try:
        if with_cases:
            queue = Queue.objects.get(pk=pk)
            cases = _coalesce_cases(queue.cases)
            return queue, cases, None
        else:
            return Queue.objects.get(pk=pk)
    except Queue.DoesNotExist:
        raise NotFoundError({'queue': 'Queue not found'})
