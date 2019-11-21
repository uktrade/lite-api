from django.db.models import Q

from conf.exceptions import NotFoundError
from queues.constants import (
    MY_TEAMS_QUEUES_CASES_ID,
    ALL_CASES_SYSTEM_QUEUE_ID,
    OPEN_CASES_SYSTEM_QUEUE_ID,
)
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum
from teams.models import Team


def _all_cases_queue():
    queue = Queue(id=ALL_CASES_SYSTEM_QUEUE_ID, name="All cases", team=Team.objects.get(name="Admin"),)
    queue.is_system_queue = True
    queue.query = Q()
    queue.reverse_ordering = True

    return queue


def _open_cases_queue():
    queue = Queue(id=OPEN_CASES_SYSTEM_QUEUE_ID, name="Open cases", team=Team.objects.get(name="Admin"),)
    queue.is_system_queue = True
    queue.query = ~Q(status__status=CaseStatusEnum.WITHDRAWN) & ~Q(status__status=CaseStatusEnum.FINALISED)

    return queue


def _all_my_team_cases_queue(team):
    queue = Queue(id=MY_TEAMS_QUEUES_CASES_ID, name="All my queues", team=team)
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
        raise NotFoundError({"queue": "Queue not found - " + str(pk)})
