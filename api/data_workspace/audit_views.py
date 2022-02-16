from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination


from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import Case
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.serializers import (
    AuditMoveCaseSerializer,
    AuditUpdatedCaseStatusSerializer,
    AuditUpdatedLicenceStatusSerializer,
)


class AuditMoveCaseListView(viewsets.ReadOnlyModelViewSet):
    """Expose 'move case' audit events to data workspace."""

    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = AuditMoveCaseSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(Case)

        # This returns a queryset of audit records for the "move case" audit event.
        # For each record, it exposes the nested "queues" JSON property as a top
        # level column called "queue" and splits into multiple rows when "queues"
        # contains multiple entries.
        # It also deals with the fact that the value of "queues" is sometimes an
        # array of queue names but sometimes a single string.
        return Audit.objects.raw(
            """
            with audit_move_case as (
              select *,
                case when jsonb_typeof(payload->'queues') = 'array'
                then payload->'queues'
                else jsonb_build_array(payload->'queues')
                end as queues
              from audit_trail_audit
              where verb = %(verb)s
              and (action_object_content_type_id = %(action_type)s
                or target_content_type_id = %(target_type)s)
              order by created_at
            )
            select *, value->>0 as "queue" from audit_move_case cross join jsonb_array_elements(queues)
            """,
            {"verb": AuditType.MOVE_CASE, "action_type": content_type.pk, "target_type": content_type.pk},
        )


class AuditUpdatedCaseStatusListView(viewsets.ReadOnlyModelViewSet):
    """Expose 'updated status' audit events to data workspace."""

    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = AuditUpdatedCaseStatusSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return Audit.objects.filter(verb=AuditType.UPDATED_STATUS).order_by("created_at")


class AuditUpdatedLicenceStatusListView(viewsets.ReadOnlyModelViewSet):
    """Expose 'licence updated status' audit events to data workspace."""

    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = AuditUpdatedLicenceStatusSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return Audit.objects.filter(verb=AuditType.LICENCE_UPDATED_STATUS).order_by("created_at")
