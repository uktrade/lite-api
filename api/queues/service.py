from typing import List, Dict

from django.db.models import Count, QuerySet

from api.cases.models import Case
from api.queues import helpers
from api.queues.constants import (
    ALL_CASES_QUEUE_ID,
    OPEN_CASES_QUEUE_ID,
    MY_TEAMS_QUEUES_CASES_ID,
    MY_ASSIGNED_CASES_QUEUE_ID,
    MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID,
    UPDATED_CASES_QUEUE_ID,
    SYSTEM_QUEUES,
)
from api.queues.models import Queue


def get_queue(pk):
    """
    Returns the specified queue (system or user created)
    """
    return next((queue for queue in get_system_queues() if queue["id"] == str(pk)), None) or helpers.get_queue(pk=pk)


def get_queues_qs(filters=None, include_team_info=True, include_case_count=False) -> QuerySet:
    """
    Returns a queryset of queues with optional team and case count information
    """
    queue_qs = (
        Queue.objects.select_related("team", "countersigning_queue").filter(**filters)
        if filters
        else Queue.objects.select_related("team", "countersigning_queue").all()
    )

    if not include_team_info:
        queue_qs = queue_qs.defer("team")

    if include_case_count:
        queue_qs = queue_qs.annotate(case_count=Count("cases"))

    return queue_qs


def get_team_queues(team_id, include_team_info=True, include_case_count=False) -> List[Dict]:
    """
    Returns a list of team queues in dictionary format with optional team and case count information
    """
    filters = {"team_id": team_id}
    return list(get_queues_qs(filters, include_team_info, include_case_count).values())


def get_system_queues(include_team_info=True, include_case_count=False, user=None) -> List[Dict]:
    """
    Returns a list of system queues in dictionary format with optional team and case count information
    """
    system_queues = []

    case_counts = _get_system_queues_case_count(user) if include_case_count and user else {}

    for id, name in SYSTEM_QUEUES.items():
        system_queue_dict = {"id": id, "name": name, "team": None}

        if not include_team_info:
            system_queue_dict.pop("team")

        if case_counts:
            system_queue_dict["case_count"] = case_counts[id]

        system_queues.append(system_queue_dict)

    return system_queues


def _get_system_queues_case_count(user) -> Dict:
    """
    Returns a dictionary of system queues and their case count
    """

    case_qs = Case.objects.submitted()

    cases_count = {
        ALL_CASES_QUEUE_ID: case_qs.count(),
        OPEN_CASES_QUEUE_ID: case_qs.is_open().count(),
        MY_TEAMS_QUEUES_CASES_ID: case_qs.in_team(team_id=user.team.id).count(),
        MY_ASSIGNED_CASES_QUEUE_ID: case_qs.assigned_to_user(user=user).not_terminal().count(),
        MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID: case_qs.assigned_as_case_officer(user=user).not_terminal().count(),
        UPDATED_CASES_QUEUE_ID: case_qs.is_updated(user=user).count(),
    }

    return cases_count
