from typing import List

from cases.models import Case
from cases.views.search.queue import SearchQueue
from queues import helpers
from queues.models import Queue

import queues.constants as queues


def get_user_created_queues():
    queue_qs = Queue.objects.all().prefetch_related("cases")
    return [SearchQueue.from_queue(queue) for queue in queue_qs]


def get_system_queues(user) -> List["SearchQueue"]:
    case_qs = Case.objects.submitted()

    return [
        SearchQueue(id=queues.ALL_CASES_QUEUE_ID, name=queues.ALL_CASES_QUEUE_NAME, cases=case_qs),
        SearchQueue(id=queues.OPEN_CASES_QUEUE_ID, name=queues.OPEN_CASES_QUEUE_NAME, cases=case_qs.is_open(),),
        SearchQueue(
            id=queues.MY_TEAMS_QUEUES_CASES_ID,
            name=queues.MY_TEAMS_QUEUES_CASES_NAME,
            cases=case_qs.in_team(team_id=user.team.id),
        ),
        SearchQueue(
            id=queues.MY_ASSIGNED_CASES_QUEUE_ID,
            name=queues.MY_ASSIGNED_CASES_QUEUE_NAME,
            cases=case_qs.assigned_to_user(user=user).not_terminal(),
        ),
        SearchQueue(
            id=queues.MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID,
            name=queues.MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_NAME,
            cases=case_qs.assigned_as_case_officer(user=user).not_terminal(),
        ),
        SearchQueue(
            id=queues.UPDATED_CASES_QUEUE_ID, name=queues.UPDATED_CASES_QUEUE_NAME, cases=case_qs.is_updated(user=user)
        ),
    ]


def get_all_queues(user):
    return get_system_queues(user=user) + get_user_created_queues()


def get_queue(user, pk):
    """
    Returns the specified queue (system or user created)
    """
    return next((queue for queue in get_system_queues(user=user) if queue.id == str(pk)), None) or helpers.get_queue(
        pk=pk
    )
