from rest_framework import generics

from cases.serializers import TinyCaseSerializer
from conf.authentication import GovAuthentication
from conf.pagination import MaxPageNumberPagination
from queues.helpers import sort_cases, filter_cases, get_queue_cases


class CasesList(generics.ListAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = TinyCaseSerializer
    pagination_class = MaxPageNumberPagination

    def get_queryset(self):
        queue_pk = self.kwargs['pk']
        team = self.request.user.team

        cases = get_queue_cases(queue_pk, team)
        cases = filter_cases(cases, self.request.query_params)
        cases = sort_cases(cases, self.request.query_params.get('sort'))

        return cases
