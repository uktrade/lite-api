from collections import defaultdict
from decimal import Decimal, InvalidOperation

import django
from django.db.models import F, When, DateField, Exists, OuterRef
from django.http import HttpResponse
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

        user = request.user.govuser
        queue_id = request.GET.get("queue_id", ALL_CASES_QUEUE_ID)
        is_work_queue = queue_id not in NON_WORK_QUEUES.keys()
        is_system_queue = queue_id in SYSTEM_QUEUES.keys()

        # we include hidden cases in non work queues (all cases, all open cases)
        # and if the flag to include hidden is added
        include_hidden = not is_work_queue or str_to_bool(request.GET.get("hidden"))
        filters = self.get_filters(request)

        page = self.paginate_queryset(
            self.get_case_queryset(user, queue_id, is_work_queue, include_hidden, filters).annotate(
                next_review_date=django.db.models.Case(
                    When(
                        case_review_date__team_id=user.team.id,
                        case_review_date__next_review_date__gte=timezone.now().date(),
                        then=F("case_review_date__next_review_date"),
                    ),
                    default=None,
                    output_field=DateField(),
                ),
                has_open_queries=Exists(
                    EcjuQuery.objects.filter(
                        case=OuterRef("pk"), raised_by_user__team_id=user.team.id, responded_at__isnull=True
                    )
                ),
            )
        )
        context = {
            "queue_id": queue_id,
            "is_system_queue": is_system_queue,
            "is_work_queue": is_work_queue,
        }

        cases = CaseListSerializer(page, context=context, team=user.team, include_hidden=include_hidden, many=True).data
        # performance
        case_map = {}
        for case in cases:
            case["destinations"] = []
            case["advice"] = defaultdict(list)
            case["denials"] = []
            case["goods"] = []
            case_map[case["id"]] = case
        # Populate certain fields outside of the serializer for performance improvements
        service.populate_goods_flags(cases)
        service.populate_destinations_flags(cases)
        service.populate_other_flags(cases)
        service.populate_organisation(cases)
        service.populate_is_recently_updated(cases)
        service.get_hmrc_sla_hours(cases)
        service.populate_activity_updates(case_map)
        service.populate_destinations(case_map)
        service.populate_good_details(case_map)
        service.populate_denials(case_map)
        service.populate_ecju_queries(case_map)
        service.populate_advice(case_map)

        # Get queue from system & my queues.
        # If this fails (i.e. I'm on a non team queue) fetch the queue data
        queues = get_system_queues(include_team_info=False, include_case_count=True, user=user) + get_team_queues(
            team_id=user.team_id, include_team_info=False, include_case_count=True
        )
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

    def head(self, request, *agrs, **kwargs):
        user = request.user.govuser
        queue_id = request.GET.get("queue_id", ALL_CASES_QUEUE_ID)
        is_work_queue = queue_id not in NON_WORK_QUEUES.keys()

        # we include hidden cases in non work queues (all cases, all open cases)
        # and if the flag to include hidden is added
        include_hidden = not is_work_queue or str_to_bool(request.GET.get("hidden"))

        filters = self.get_filters(request)

        count = self.get_case_queryset(user, queue_id, is_work_queue, include_hidden, filters).count()

        response = HttpResponse()
        response.headers["Resource-Count"] = count
        return response

    def get_case_queryset(self, user, queue_id, is_work_queue, include_hidden, filters):
        return Case.objects.search(
            queue_id=queue_id,
            is_work_queue=is_work_queue,
            user=user,
            include_hidden=include_hidden,
            **filters,
        )

    def get_filters(self, request):
        filters = {key: value for key, value in request.GET.items() if key not in ["hidden", "queue_id", "flags"]}

        search_tabs = ("my_cases", "open_queries")
        selected_tab = request.GET.get("selected_tab")
        if selected_tab and selected_tab in search_tabs:
            filters[selected_tab] = True

        if "max_total_value" in filters:
            try:
                filters["max_total_value"] = Decimal(filters["max_total_value"])
            except (InvalidOperation, TypeError):
                del filters["max_total_value"]

        filters["flags"] = request.GET.getlist("flags", [])
        filters["regime_entry"] = [regime for regime in request.GET.getlist("regime_entry", []) if regime]
        filters["exclude_regime_entry"] = request.GET.get("exclude_regime_entry", False)
        filters["control_list_entry"] = [cle for cle in request.GET.getlist("control_list_entry", []) if cle]
        filters["exclude_control_list_entry"] = request.GET.get("exclude_control_list_entry", False)
        filters["assigned_queues"] = request.GET.getlist("assigned_queues", [])
        filters["submitted_from"] = make_date_from_params("submitted_from", filters)
        filters["submitted_to"] = make_date_from_params("submitted_to", filters)
        filters["finalised_from"] = make_date_from_params("finalised_from", filters)
        filters["finalised_to"] = make_date_from_params("finalised_to", filters)
        filters["countries"] = request.GET.getlist("countries", [])

        return filters
