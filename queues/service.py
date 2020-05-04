from typing import List, Dict

from django.db.models import Count, QuerySet

from cases.models import Case
from queues import helpers
from queues.constants import (
    ALL_CASES_QUEUE_ID,
    OPEN_CASES_QUEUE_ID,
    MY_TEAMS_QUEUES_CASES_ID,
    MY_ASSIGNED_CASES_QUEUE_ID,
    MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID,
    UPDATED_CASES_QUEUE_ID,
    SYSTEM_QUEUES,
)
from queues.models import Queue


def get_system_queues(include_team=True, include_case_count=False, user=None) -> List[Dict]:
    """
    Returns a list of system queues in dictionary format with optional team and case count information
    """
    system_queues = []

    case_counts = get_cases_count(user) if include_case_count and user else {}

    for id, name in SYSTEM_QUEUES.items():
        system_queue_dict = {"id": id, "name": name, "team": None}

        if not include_team:
            system_queue_dict.pop("team")

        if case_counts:
            system_queue_dict["case_count"] = case_counts[id]

        system_queues.append(system_queue_dict)

    return system_queues


def get_cases_count(user) -> Dict:
    case_qs = Case.objects.submitted()
    get_cases_count = {
        ALL_CASES_QUEUE_ID: case_qs.count(),
        OPEN_CASES_QUEUE_ID: case_qs.is_open().count(),
        MY_TEAMS_QUEUES_CASES_ID: case_qs.in_team(team_id=user.team.id).count(),
        MY_ASSIGNED_CASES_QUEUE_ID: case_qs.assigned_to_user(user=user).not_terminal().count(),
        MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID: case_qs.assigned_as_case_officer(user=user).not_terminal().count(),
        UPDATED_CASES_QUEUE_ID: case_qs.is_updated(user=user).count(),
    }

    return get_cases_count


def get_work_queues_qs(include_team=True, include_case_count=False) -> QuerySet:
    queue_qs = Queue.objects.all()

    if not include_team:
        queue_qs = queue_qs.defer("team")

    if include_case_count:
        queue_qs = queue_qs.annotate(case_count=Count("cases"))

    return queue_qs


def get_work_queues(include_team=True, include_case_count=False) -> List[Dict]:
    return list(get_work_queues_qs(include_team, include_case_count).values())


def get_all_queues(include_team=True, include_case_count=False, user=None) -> List[Dict]:
    """
    Returns all queues with the values id, name, optional case_count and optional team
    """
    return get_system_queues(include_team, include_case_count, user) + get_work_queues(include_team, include_case_count)


def get_queue(pk):
    """
    Returns the specified queue (system or user created)
    """
    return next((queue for queue in get_system_queues() if queue["id"] == str(pk)), None) or helpers.get_queue(pk=pk)
