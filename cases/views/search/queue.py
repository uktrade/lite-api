from typing import List

from cases.models import Case
from queues.models import Queue
from teams.models import Team

import queues.constants as queues


class SearchQueue:
    """
    A SearchQueue is a representation of a Queue or a system Queue 😀
    """

    def __init__(self, id, name, cases):
        self.id = id
        self.name = name
        self.cases = cases

    @classmethod
    def from_queue(cls, queue) -> "SearchQueue":
        return cls(
            id=queue.id, name=queue.name, cases=queue.cases
        )

    @classmethod
    def get_user_created_queues(cls):
        queue_qs = Queue.objects.all().prefetch_related("cases")
        return [cls.from_queue(queue) for queue in queue_qs]

    @classmethod
    def get_system_queues(cls, user) -> List["SearchQueue"]:
        case_qs = Case.objects.submitted()

        return [
            cls(
                id=queues.ALL_CASES_QUEUE_ID,
                name=queues.ALL_CASES_QUEUE_NAME,
                cases=case_qs
            ),
            cls(
                id=queues.OPEN_CASES_QUEUE_ID,
                name=queues.OPEN_CASES_QUEUE_NAME,
                cases=case_qs.is_open(),
            ),
            cls(
                id=queues.MY_TEAMS_QUEUES_CASES_ID,
                name=queues.MY_TEAMS_QUEUES_CASES_NAME,
                cases=case_qs.in_team(team_id=user.team.id)
            ),
            cls(
                id=queues.MY_ASSIGNED_CASES_QUEUE_ID,
                name=queues.MY_ASSIGNED_CASES_QUEUE_NAME,
                cases=case_qs.assigned_to_user(user=user).not_terminal()
            ),
            cls(
                id=queues.MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID,
                name=queues.MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_NAME,
                cases=case_qs.assigned_as_case_officer(user=user).not_terminal()
            ),
            cls(
                id=queues.UPDATED_CASES_QUEUE_ID,
                name=queues.UPDATED_CASES_QUEUE_NAME,
                cases=case_qs.is_updated(user=user)
            ),
        ]

    @classmethod
    def get_all_queues(cls, user):
        return cls.get_system_queues(user=user) + cls.get_user_created_queues()