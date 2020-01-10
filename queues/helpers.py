from django.db.models import Q

from cases.helpers import get_updated_case_ids, get_assigned_as_case_officer_case_ids, get_assigned_to_user_case_ids
from conf.exceptions import NotFoundError
from queues.models import Queue
from teams.models import Team
from users.models import GovUser

import queues.constants as queues


def _all_cases_queue():
    queue = Queue(id=queues.ALL_CASES_QUEUE_ID, name=queues.ALL_CASES_QUEUE_NAME, team=Team.objects.get(name="Admin"))
    queue.is_system_queue = True
    queue.query = Q()
    queue.reverse_ordering = True

    return queue


def _open_cases_queue():
    queue = Queue(id=queues.OPEN_CASES_QUEUE_ID, name=queues.OPEN_CASES_QUEUE_NAME, team=Team.objects.get(name="Admin"))
    queue.is_system_queue = True
    queue.query = Q(status__is_terminal=False)

    return queue


def _updated_cases_queue(user: GovUser):
    queue = Queue(
        id=queues.UPDATED_CASES_QUEUE_ID, name=queues.UPDATED_CASES_QUEUE_NAME, team=Team.objects.get(name="Admin")
    )
    queue.is_system_queue = True
    updated_case_ids = get_updated_case_ids(user)
    queue.query = Q(id__in=updated_case_ids)
    queue.reverse_ordering = True

    return queue


def _my_assigned_cases_queue(user: GovUser):
    queue = Queue(
        id=queues.MY_ASSIGNED_CASES_QUEUE_ID,
        name=queues.MY_ASSIGNED_CASES_QUEUE_NAME,
        team=Team.objects.get(name="Admin"),
    )
    queue.is_system_queue = True
    assigned_to_user_case_ids = get_assigned_to_user_case_ids(user)
    queue.query = Q(id__in=assigned_to_user_case_ids, status__is_terminal=False)

    return queue


def _my_case_officer_cases_queue(user: GovUser):
    queue = Queue(
        id=queues.MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID,
        name=queues.MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_NAME,
        team=Team.objects.get(name="Admin"),
    )
    queue.is_system_queue = True
    assigned_as_case_officer_case_ids = get_assigned_as_case_officer_case_ids(user)
    queue.query = Q(id__in=assigned_as_case_officer_case_ids, status__is_terminal=False)

    return queue


def _my_team_cases_queue(team: Team):
    queue = Queue(id=queues.MY_TEAMS_QUEUES_CASES_ID, name=queues.MY_TEAMS_QUEUES_CASES_NAME, team=team)
    queue.is_system_queue = True
    my_team_queues = Queue.objects.filter(team=team)
    queue.query = Q(queues__in=my_team_queues)

    return queue


def get_queues(include_system_queues=False, user: GovUser = None):
    """
    Returns all queues
    Optionally returns system queues
    """
    queues = Queue.objects.all()

    if include_system_queues:
        queues = list(queues)
        queues.append(_all_cases_queue())
        queues.append(_open_cases_queue())
        if user:
            queues.append(_my_team_cases_queue(team=user.team))
            queues.append(_my_assigned_cases_queue(user=user))
            queues.append(_my_case_officer_cases_queue(user=user))
            queues.append(_updated_cases_queue(user=user))

    return queues


def get_queue(pk, user: GovUser = None):
    """
    Returns the specified queue
    """
    queues = get_queues(include_system_queues=True, user=user)
    queue = [queue for queue in queues if str(queue.id) == str(pk)]

    if queue:
        return queue[0]
    else:
        raise NotFoundError({"queue": "Queue not found - " + str(pk)})
