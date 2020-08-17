import django
from django.db.models import F, When, DateField, Exists, OuterRef
from django.utils import timezone
from rest_framework import generics

from api.cases.libraries.dates import make_date_from_params
from api.cases.models import Case, EcjuQuery
from api.cases.serializers import CaseListSerializer
from api.cases.views.search import service
from api.core.authentication import GovAuthentication
from api.core.helpers import str_to_bool
from api.queues.constants import SYSTEM_QUEUES, ALL_CASES_QUEUE_ID, NON_WORK_QUEUES
from api.queues.models import Queue
from api.queues.service import get_system_queues, get_team_queues


class CasesSearchView(generics.ListAPIView):
    """
    Provides a search view for the Case model.
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request, *args, **kwargs):
        queue_id = request.GET.get("queue_id", ALL_CASES_QUEUE_ID)
        is_work_queue = queue_id not in NON_WORK_QUEUES.keys()
        is_system_queue = queue_id in SYSTEM_QUEUES.keys()

        context = {
            "queue_id": queue_id,
            "is_system_queue": is_system_queue,
            "is_work_queue": is_work_queue,
        }

        # we include hidden cases in non work queues (all cases, all open cases)
        # and if the flag to include hidden is added
        include_hidden = not is_work_queue or str_to_bool(request.GET.get("hidden"))
        filters = {key: value for key, value in request.GET.items() if key not in ["hidden", "queue_id", "flags"]}

        filters["flags"] = request.GET.getlist("flags", [])
        filters["submitted_from"] = make_date_from_params("submitted_from", filters)
        filters["submitted_to"] = make_date_from_params("submitted_to", filters)
        filters["finalised_from"] = make_date_from_params("finalised_from", filters)
        filters["finalised_to"] = make_date_from_params("finalised_to", filters)

        page = self.paginate_queryset(
            Case.objects.search(
                queue_id=queue_id,
                is_work_queue=is_work_queue,
                user=request.user,
                include_hidden=include_hidden,
                **filters,
            ).annotate(
                next_review_date=django.db.models.Case(
                    When(
                        case_review_date__team_id=request.user.team.id,
                        case_review_date__next_review_date__gte=timezone.now().date(),
                        then=F("case_review_date__next_review_date"),
                    ),
                    default=None,
                    output_field=DateField(),
                ),
                has_open_queries=Exists(
                    EcjuQuery.objects.filter(
                        case=OuterRef("pk"), raised_by_user__team_id=request.user.team.id, responded_at__isnull=True
                    )
                ),
            )
        )

        queues = get_system_queues(
            include_team_info=False, include_case_count=True, user=request.user
        ) + get_team_queues(team_id=request.user.team_id, include_team_info=False, include_case_count=True)

        cases = CaseListSerializer(
            page, context=context, team=request.user.team, include_hidden=include_hidden, many=True
        ).data

        # Populate certain fields outside of the serializer for performance improvements
        service.populate_goods_flags(cases)
        service.populate_destinations_flags(cases)
        service.populate_other_flags(cases)
        service.populate_organisation(cases)
        service.populate_is_recently_updated(cases)
        service.get_hmrc_sla_hours(cases)

        # Get queue from system & my queues.
        # If this fails (i.e. I'm on a non team queue) fetch the queue data
        queue = (
            next((q for q in queues if str(q["id"]) == str(queue_id)), None)
            or Queue.objects.filter(id=queue_id).values()[0]
        )

        statuses = service.get_case_status_list()
        case_types = service.get_case_type_type_list()
        gov_users = service.get_gov_users_list()
        advice_types = service.get_advice_types_list()

        return self.get_paginated_response(
            {
                "queues": queues,
                "cases": cases,
                "filters": {
                    "statuses": statuses,
                    "case_types": case_types,
                    "gov_users": gov_users,
                    "advice_types": advice_types,
                },
                "is_system_queue": context["is_system_queue"],
                "is_work_queue": is_work_queue,
                "queue": queue,
            }
        )
