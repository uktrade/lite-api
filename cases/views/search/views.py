from rest_framework import generics

from cases.enums import CaseTypeEnum
from cases.libraries.dates import make_date_from_params
from cases.models import Case
from cases.serializers import CaseListSerializer
from cases.views.search import service
from conf.authentication import GovAuthentication
from conf.helpers import str_to_bool
from queues.constants import SYSTEM_QUEUES, ALL_CASES_QUEUE_ID, NON_WORK_QUEUES
from queues.service import get_all_queues


class CasesSearchView(generics.ListAPIView):
    """
    Provides a search view for the Case model.
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request, *args, **kwargs):
        queue_id = request.GET.get("queue_id", ALL_CASES_QUEUE_ID)
        is_work_queue = queue_id not in NON_WORK_QUEUES.keys()
        context = {
            "is_system_queue": queue_id in SYSTEM_QUEUES.keys(),
            "queue_id": queue_id,
            "is_work_queue": is_work_queue,
        }

        # we include hidden cases in non work queues (all cases, all open cases)
        # and if the flag to include hidden is added
        include_hidden = not is_work_queue or str_to_bool(request.GET.get("hidden"))
        filters = {key.replace("filters.", ""): value for key, value in request.GET.items() if key.startswith("filters.")}

        filters["submitted_from"] = make_date_from_params("submitted_from", filters)
        filters["submitted_to"] = make_date_from_params("submitted_to", filters)

        page = self.paginate_queryset(
            Case.objects.search(
                queue_id=queue_id,
                is_work_queue=is_work_queue,
                user=request.user,
                include_hidden=include_hidden,
                **filters
            )
        )
        queues = get_all_queues(include_team=False, include_case_count=True, user=request.user)
        cases = CaseListSerializer(
            page, context=context, team=request.user.team, include_hidden=include_hidden, many=True
        ).data

        service.populate_is_recently_updated(cases)
        service.get_hmrc_sla_hours(cases)

        queue = next((q for q in queues if str(q["id"]) == str(queue_id)))

        statuses = service.get_case_status_list()
        case_types = service.get_case_type_type_list()
        gov_users = service.get_gov_users_list()
        advice_types = service.get_advice_types_list()

        return self.get_paginated_response(
            {
                "queues": queues,
                "cases": cases,
                "filters": {"statuses": statuses, "case_types": case_types, "gov_users": gov_users, "advice_types": advice_types},
                "is_system_queue": context["is_system_queue"],
                "is_work_queue": is_work_queue,
                "queue": queue,
            }
        )
