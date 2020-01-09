from typing import List

from cases.models import Case
from queues.models import Queue
from teams.models import Team

import queues.constants as queues


class SearchQueue:
    """
    A SearchQueue is a representation of a Queue or a system Queue.
    """

    def __init__(self, id, name, team, case_count):
        self.id = id
        self.name = name
        self.team = team
        self.case_count = case_count

    @classmethod
    def from_queue(cls, queue, case_qs=None) -> "SearchQueue":
        if not case_qs:
            case_qs = Case.objects.all()

        return cls(
            id=queue.id, name=queue.name, team=queue.team, case_count=case_qs.in_queue(queue_id=queue.id).count(),
        )

    @classmethod
    def system(cls, user=None, team=None, case_qs=None) -> List["SearchQueue"]:
        if not case_qs:
            case_qs = Case.objects.all()

        return [
            cls(
                id=queues.ALL_CASES_SYSTEM_QUEUE_ID,
                name=queues.ALL_CASES_SYSTEM_QUEUE_NAME,
                team=Team.objects.get(name="Admin"),
                case_count=case_qs.count(),
            ),
            cls(
                id=queues.OPEN_CASES_SYSTEM_QUEUE_ID,
                name=queues.OPEN_CASES_SYSTEM_QUEUE_NAME,
                team=Team.objects.get(name="Admin"),
                case_count=case_qs.is_open().count(),
            ),
            cls(
                id=queues.MY_TEAMS_QUEUES_CASES_ID,
                name=queues.MY_TEAMS_QUEUES_CASES_NAME,
                team=Team.objects.get(name="Admin"),
                case_count=case_qs.in_team(team=team).count(),
            ),
            cls(
                id=queues.UPDATED_CASES_QUEUE_ID,
                name=queues.UPDATED_CASES_QUEUE_NAME,
                team=Team.objects.get(name="Admin"),
                case_count=case_qs.is_updated(user=user).count(),
            ),
        ]

    @classmethod
    def all(cls, user=None, team=None, case_qs=None, queue_qs=None):
        return cls.system(user=user, team=team, case_qs=case_qs) + cls.from_queue_qs(queue_qs)

    @classmethod
    def from_queue_qs(cls, queue_qs=None):
        if not queue_qs:
            queue_qs = Queue.objects.all()

        return [cls.from_queue(queue) for queue in queue_qs]
