from django.contrib.contenttypes.models import ContentType
from django.db import connection
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination


from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import Case
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v1.serializers import (
    AuditBulkApprovalRecommendationSerializer,
    AuditMoveCaseSerializer,
    AuditUpdatedCaseStatusSerializer,
    AuditUpdatedLicenceStatusSerializer,
)


class AuditMoveCaseRawQuerySet:
    # This is pretty horrible but it solves a problem in the "simplest way"
    # Originally this was just Audit.objects.raw which then gets sent through
    # DRFs gubbins to get a paginated queryset.
    #
    # The problem here is that by default the raw queryset is going to bring
    # back the entire resultset to get both the count and the paginated results.
    #
    # In the case for this endpoint we're looping through 10,000s of rows,
    # which was then transforming all of those rows into actual Audit objects
    # putting them in a list and then doing len() and [0:25] on those lists.
    #
    # This was all hugely inefficient and wasteful.
    #
    # This horrible queryset allows us to just provide the paginator with what
    # it needs quickly and efficiently.
    #
    # This could have been achieved by overriding a whole bunch in the APIView
    # itself but that would have taken a lot more code and in this case we get
    # to keep using what DRF wants to do internally.

    def count(self):
        content_type = ContentType.objects.get_for_model(Case)
        with connection.cursor() as cursor:
            cursor.execute(
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
                select count(*) from audit_move_case cross join jsonb_array_elements(queues)""",
                {"verb": AuditType.MOVE_CASE, "action_type": content_type.pk, "target_type": content_type.pk},
            )
            row = cursor.fetchone()
        return row[0]

    def __getitem__(self, slice):
        content_type = ContentType.objects.get_for_model(Case)
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
            select *, value->>0 as "queue" from audit_move_case cross join jsonb_array_elements(queues) LIMIT %(limit)s OFFSET %(offset)s
            """,
            {
                "verb": AuditType.MOVE_CASE,
                "action_type": content_type.pk,
                "target_type": content_type.pk,
                "offset": slice.start,
                "limit": slice.stop - slice.start,
            },
        )


class AuditMoveCaseListView(viewsets.ReadOnlyModelViewSet):
    """Expose 'move case' audit events to data workspace."""

    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = AuditMoveCaseSerializer
    pagination_class = LimitOffsetPagination
    queryset = AuditMoveCaseRawQuerySet()


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


class AuditBulkApprovalRecommendationListView(viewsets.ReadOnlyModelViewSet):
    """Expose 'bulk approval recommendation' audit events to data workspace."""

    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = AuditBulkApprovalRecommendationSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return Audit.objects.filter(verb=AuditType.CREATE_BULK_APPROVAL_RECOMMENDATION).order_by("created_at")
