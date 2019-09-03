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
        pk = self.kwargs['pk']
        team = self.request.user.team

        queue, cases = get_queue(pk=pk, return_cases=True, team=team)
        cases = filter_cases(cases, self.request.query_params)
        cases = sort_cases(cases, self.request.query_params.get('sort'))

        return cases
