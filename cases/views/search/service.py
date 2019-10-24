from typing import List, Dict

from django.db.models.functions import Coalesce

from cases.enums import CaseType
from cases.models import Case
from cases.serializers import TinyCaseSerializer
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum


def get_user_queue_meta(user) -> List[Dict]:
    """
    Retrieves meta information on all the queues available for a user.
    """
    case_qs = Case.objects.all()

    return [
        {
            'id': 'all_cases',
            'href': '/cases/?is_system_queue=true',
            'name': 'All cases',
            'case_count': case_qs.count(),
        },
        {
            'id': 'open_cases',
            'href': '/cases/?is_system_queue=true&status=open',
            'name': 'Open cases',
            'case_count': case_qs.is_open().count(),
        },
        {
            'id': 'team_cases',
            'href': '/cases/?is_system_queue=true&team=true',
            'name': 'All my queues',
            'case_count': case_qs.in_team(team=user.team).count(),
        },
    ] + [
        {
            'id': str(queue.id),
            'href': f'/cases/?title={queue.name}&queue={queue.id}',
            'name': queue.name,
            'case_count': case_qs.in_queue(queue_id=queue.id).count(),
        } for queue in Queue.objects.all()
    ]


def search_cases(queue_id=None, team=None, status=None, case_type=None, sort=None):
    """
    Search for a user's available cases given a set of search parameters.
    """
    case_qs = Case.objects.all()

    if queue_id:
        case_qs = case_qs.in_queue(queue_id=queue_id)

    if team:
        case_qs = case_qs.in_team(team=team)

    if status:
        if status == 'open':
            # Special status for all open. Does not exist in CaseStatusEnum.
            case_qs = case_qs.is_open()
        else:
            case_qs = case_qs.has_status(status=status)

    if case_type:
        case_qs = case_qs.is_type(case_type=case_type)

    case_qs = case_qs.order_by_date()

    if sort:
        case_qs = case_qs.order_by_status(order='-' if '-' in sort else '')

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
