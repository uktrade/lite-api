from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import filters

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import Case
from api.users.models import ExporterUser, GovUser


class AuditEventCaseFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        pk = view.kwargs["pk"]
        content_type = ContentType.objects.get_for_model(Case)
        queryset = Audit.objects.filter(
            Q(action_object_object_id=pk, action_object_content_type=content_type)
            | Q(target_object_id=pk, target_content_type=content_type)
        )
        return queryset


class AuditEventTeamFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        team = request.query_params.get("team_id")
        if not team:
            return queryset

        gov_content_type = ContentType.objects.get_for_model(GovUser)
        user_ids = queryset.filter(actor_content_type=gov_content_type).values_list("actor_object_id", flat=True)
        team_user_ids = GovUser.objects.filter(pk__in=list(user_ids), team=team).values_list("pk", flat=True)
        return queryset.filter(actor_object_id__in=list(team_user_ids))


class AuditEventExporterUserFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        user_type = request.query_params.get("user_type")
        if not user_type:
            return queryset

        user_type_content_type = ContentType.objects.get_for_model(ExporterUser)
        return queryset.filter(actor_content_type=user_type_content_type)


class AuditEventMentionsFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        audit_type = request.query_params.get("activity_type")
        if not audit_type:
            return queryset

        return queryset.filter(verb=AuditType.CREATED_CASE_NOTE_WITH_MENTIONS)
