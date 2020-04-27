from typing import List

from django.db.models import Count

from cases.models import Case
from queues import helpers
from queues.models import Queue

import queues.constants as queues


def get_system_queues(user) -> List:
    case_qs = Case.objects.submitted()

    return [
        {"id": queues.ALL_CASES_QUEUE_ID, "name": queues.ALL_CASES_QUEUE_NAME, "case_count": case_qs.count()},
        {
            "id": queues.OPEN_CASES_QUEUE_ID,
            "name": queues.OPEN_CASES_QUEUE_NAME,
            "case_count": case_qs.is_open().count(),
        },
        {
            "id": queues.MY_TEAMS_QUEUES_CASES_ID,
            "name": queues.MY_TEAMS_QUEUES_CASES_NAME,
            "case_count": case_qs.in_team(team_id=user.team.id).count(),
        },
        {
            "id": queues.MY_ASSIGNED_CASES_QUEUE_ID,
            "name": queues.MY_ASSIGNED_CASES_QUEUE_NAME,
            "case_count": case_qs.assigned_to_user(user=user).not_terminal().count(),
        },
        {
            "id": queues.MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID,
            "name": queues.MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_NAME,
            "case_count": case_qs.assigned_as_case_officer(user=user).not_terminal().count(),
        },
        {
            "id": queues.UPDATED_CASES_QUEUE_ID,
            "name": queues.UPDATED_CASES_QUEUE_NAME,
            "case_count": case_qs.is_updated(user=user).count(),
        },
    ]


def get_queues():
    return list(
        Queue.objects.annotate(case_count=Count("cases")).values("id", "name", "case_count")
    )


def get_all_queues(user):
    """
    Returns all queues with the values id, name & case_count
    """
    return get_system_queues(user=user) + get_queues()


def get_queue(user, pk):
    """
    Returns the specified queue (system or user created)
    """
    return next((queue for queue in get_system_queues(user=user) if queue["id"] == str(pk)), None) or helpers.get_queue(
        pk=pk
    )
