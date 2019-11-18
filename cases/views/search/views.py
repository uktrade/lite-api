from rest_framework import generics

from cases.models import Case
from cases.serializers import TinyCaseSerializer
from cases.views.search import service
from cases.views.search.serializers import SearchQueueSerializer
from conf.authentication import GovAuthentication
from conf.pagination import MaxPageNumberPagination
from queues.constants import SYSTEM_QUEUES, ALL_CASES_SYSTEM_QUEUE_ID


class CasesSearchView(generics.ListAPIView):
    """
    Provides a search view for the Case model.
    """

    authentication_classes = (GovAuthentication,)
    pagination_class = MaxPageNumberPagination

    def get(self, request, *args, **kwargs):
        queue_id = request.GET.get("queue_id", ALL_CASES_SYSTEM_QUEUE_ID)
        context = {"is_system_queue": queue_id in SYSTEM_QUEUES, "queue_id": queue_id}

        page = self.paginate_queryset(
            Case.objects.search(
                queue_id=queue_id,
                team=request.user.team,
                status=request.GET.get("status"),
                case_type=request.GET.get("case_type"),
                sort=request.GET.get("sort"),
                date_order="-" if queue_id in SYSTEM_QUEUES else "",
            )
        )
        queues = SearchQueueSerializer(service.get_search_queues(team=request.user.team), many=True).data
        cases = TinyCaseSerializer(page, context=context, team=request.user.team, many=True).data
        statuses = service.get_case_status_list()
        case_types = service.get_case_type_list()
        queue = next(q for q in queues if q["id"] == queue_id)

        return self.get_paginated_response(
            {
                "queues": queues,
                "cases": cases,
                "filters": {"statuses": statuses, "case_types": case_types,},
                "is_system_queue": context["is_system_queue"],
                "queue": queue,
            }
        )
