from rest_framework import generics

from cases.serializers import TinyCaseSerializer
from conf.authentication import GovAuthentication
from conf.pagination import MaxPageNumberPagination
from queues.helpers import get_queue, sort_cases, filter_cases


class CasesList(generics.ListAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = TinyCaseSerializer
    pagination_class = MaxPageNumberPagination

    def get_queryset(self):
        queue_pk = self.kwargs['pk']
        team = self.request.user.team

        queue = get_queue(queue_pk, team)
        cases = filter_cases(queue.get_cases(), self.request.query_params)
        # cases = sort_cases(cases, self.request.query_params.get('sort'))

        return cases.distinct()
