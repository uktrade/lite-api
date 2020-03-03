from rest_framework import generics

from cases.enums import CaseTypeEnum
from cases.models import Case
from cases.serializers import CaseListSerializer
from cases.views.search import service
from cases.views.search.serializers import SearchQueueSerializer
from conf.authentication import GovAuthentication
from queues.constants import SYSTEM_QUEUES, ALL_CASES_QUEUE_ID, OPEN_CASES_QUEUE_ID


class CasesSearchView(generics.ListAPIView):
    """
    Provides a search view for the Case model.
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request, *args, **kwargs):
        queue_id = request.GET.get("queue_id", ALL_CASES_QUEUE_ID)
        context = {"is_system_queue": queue_id in SYSTEM_QUEUES, "queue_id": queue_id}
        order = "-" if queue_id == ALL_CASES_QUEUE_ID or queue_id == OPEN_CASES_QUEUE_ID else ""

        page = self.paginate_queryset(
            Case.objects.search(
                queue_id=queue_id,
                user=request.user,
                status=request.GET.get("status"),
                case_type=CaseTypeEnum.reference_to_id(request.GET.get("case_type")),
                assigned_user=request.GET.get("assigned_user"),
                case_officer=request.GET.get("case_officer"),
                sort=request.GET.get("sort"),
                date_order=order,
            )
        )
        queues = SearchQueueSerializer(service.get_search_queues(user=request.user), many=True).data
        cases = CaseListSerializer(page, context=context, team=request.user.team, many=True).data
        queue = next(q for q in queues if q["id"] == queue_id)

        statuses = service.get_case_status_list()
        case_types = service.get_case_type_type_list()
        gov_users = service.get_gov_users_list()

        return self.get_paginated_response(
            {
                "queues": queues,
                "cases": cases,
                "filters": {"statuses": statuses, "case_types": case_types, "gov_users": gov_users},
                "is_system_queue": context["is_system_queue"],
                "queue": queue,
            }
        )
