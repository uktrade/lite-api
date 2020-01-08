from django.db.models import Q

from cases.helpers import get_updated_case_ids
from conf.exceptions import NotFoundError
from queues.constants import (
    MY_TEAMS_QUEUES_CASES_ID,
    ALL_CASES_SYSTEM_QUEUE_ID,
    OPEN_CASES_SYSTEM_QUEUE_ID,
    UPDATED_CASES_QUEUE_ID,
)
from queues.models import Queue
from static.statuses.enums import CaseStatusEnum
from teams.models import Team
from users.models import GovUser


def _all_cases_queue():
    queue = Queue(id=ALL_CASES_SYSTEM_QUEUE_ID, name="All cases", team=Team.objects.get(name="Admin"))
    queue.is_system_queue = True
    queue.query = Q()
    queue.reverse_ordering = True

    return queue


def _open_cases_queue():
    queue = Queue(id=OPEN_CASES_SYSTEM_QUEUE_ID, name="Open cases", team=Team.objects.get(name="Admin"))
    queue.is_system_queue = True
    queue.query = ~Q(status__status__in=[CaseStatusEnum.WITHDRAWN, CaseStatusEnum.FINALISED])

    return queue


def _updated_cases_queue(user: GovUser):
    queue = Queue(id=UPDATED_CASES_QUEUE_ID, name="New Exporter Amendments", team=Team.objects.get(name="Admin"))
    queue.is_system_queue = True
    updated_case_ids = get_updated_case_ids(user)
    queue.query = Q(id__in=updated_case_ids)
    queue.reverse_ordering = True

    return queue


def _all_my_team_cases_queue(team: Team):
    queue = Queue(id=MY_TEAMS_QUEUES_CASES_ID, name="All my queues", team=team)
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
        queues.insert(0, _all_cases_queue())
        queues.insert(1, _open_cases_queue())
        if user:
            queues.insert(2, _all_my_team_cases_queue(team=user.team))
            queues.insert(3, _updated_cases_queue(user=user))

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
