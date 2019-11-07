from typing import List

from cases.models import Case
from queues.constants import ALL_CASES_SYSTEM_QUEUE_ID, MY_TEAMS_QUEUES_CASES_ID, OPEN_CASES_SYSTEM_QUEUE_ID
from queues.models import Queue
from teams.models import Team


class SearchQueue:
    def __init__(self, id, name, team, case_count):
        self.id = id
        self.name = name
        self.team = team
        self.case_count = case_count

    @classmethod
    def from_queue(cls, queue, case_qs=None) -> 'SearchQueue':
        if not case_qs:
            case_qs = Case.objects.all()

        return cls(
            id=queue.id,
            name=queue.name,
            team=queue.team,
            case_count=case_qs.in_queue(queue_id=queue.id).count(),
        )

    @classmethod
    def system(cls, team, case_qs=None) -> List['SearchQueue']:
        if not case_qs:
            case_qs = Case.objects.all()

        return [
            cls(
                id=ALL_CASES_SYSTEM_QUEUE_ID,
                name='All cases',
                team=Team.objects.get(name='Admin'),
                case_count=case_qs.count(),
            ),
            cls(
                id=OPEN_CASES_SYSTEM_QUEUE_ID,
                name='Open cases',
                team=Team.objects.get(name='Admin'),
                case_count=case_qs.is_open().count()
            ),
            cls(
                id=MY_TEAMS_QUEUES_CASES_ID,
                name='My cases',
                team=Team.objects.get(name='Admin'),
                case_count=case_qs.in_team(team=team).count()
            ),
        ]

    @classmethod
    def all(cls, team, case_qs=None, queue_qs=None):
        return cls.system(team, case_qs) + cls.from_queue_qs(queue_qs)

    @classmethod
    def from_queue_qs(cls, queue_qs=None):
        if not queue_qs:
            queue_qs = Queue.objects.all()

        return [cls.from_queue(queue) for queue in queue_qs]
