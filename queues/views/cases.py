from rest_framework import generics

from cases.serializers import TinyCaseSerializer
from conf.authentication import GovAuthentication
from conf.pagination import MaxPageNumberPagination
from queues.constants import (
    ALL_CASES_SYSTEM_QUEUE_ID,
    OPEN_CASES_SYSTEM_QUEUE_ID,
    MY_TEAMS_QUEUES_CASES_ID,
)
from queues.helpers import get_queue, sort_cases, filter_cases


class CasesList(generics.ListAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = TinyCaseSerializer
    pagination_class = MaxPageNumberPagination

    def get_queryset(self):
        queue_pk = self.kwargs["pk"]
        team = self.request.user.team

        queue = get_queue(queue_pk, team)
        cases = filter_cases(queue.get_cases(), self.request.query_params)
        cases = sort_cases(cases, self.request.query_params.get("sort"))

        return cases.distinct()

    def get_serializer_context(self):
        # Identify the queue meta here so it is not called multiple times in the serializer
        is_system_queue = str(self.kwargs["pk"]) in [
            ALL_CASES_SYSTEM_QUEUE_ID,
            OPEN_CASES_SYSTEM_QUEUE_ID,
            MY_TEAMS_QUEUES_CASES_ID,
        ]
        return {
            "queue": get_queue(self.kwargs["pk"]).name,
            "is_system_queue": is_system_queue,
        }
