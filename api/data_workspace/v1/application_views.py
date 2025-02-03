from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from django.db.models import Prefetch, Q

from api.applications import models
from api.applications.serializers import standard_application, good, party, denial
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.parties.enums import PartyType


class StandardApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = standard_application.StandardApplicationDataWorkspaceSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.StandardApplication.objects.prefetch_related(
        Prefetch(
            "parties",
            queryset=models.PartyOnApplication.objects.filter(
                deleted_at__isnull=True,
                party__type=PartyType.END_USER,
            ).select_related("party"),
            to_attr="end_users",
        ),
        Prefetch(
            "audit_trail",
            queryset=Audit.objects.filter(
                verb=AuditType.UPDATED_APPLICATION_NAME,
            ),
            to_attr="is_reference_update_audits",
        ),
        Prefetch(
            "audit_trail",
            queryset=Audit.objects.filter(
                verb=AuditType.REMOVE_GOOD_FROM_APPLICATION,
            ),
            to_attr="is_product_removed_audits",
        ),
        Prefetch(
            "audit_trail",
            queryset=Audit.objects.filter(
                Q(
                    verb__in=[
                        AuditType.ADDED_APPLICATION_LETTER_REFERENCE,
                        AuditType.UPDATE_APPLICATION_LETTER_REFERENCE,
                        AuditType.REMOVED_APPLICATION_LETTER_REFERENCE,
                    ]
                )
            ),
            to_attr="app_letter_ref_updated_audits",
        ),
        Prefetch(
            "audit_trail",
            queryset=Audit.objects.filter(verb=AuditType.UPDATED_STATUS),
            to_attr="updated_status_audits",
        ),
    )


class GoodOnApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = good.GoodOnApplicationDataWorkspaceSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GoodOnApplication.objects.all()


class GoodOnApplicationControlListEntriesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = good.GoodOnApplicationControlListEntrySerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GoodOnApplicationControlListEntry.objects.all()


class GoodOnApplicationRegimeEntriesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = good.GoodOnApplicationRegimeEntrySerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GoodOnApplicationRegimeEntry.objects.all()


class PartyOnApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = party.PartyOnApplicationViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.PartyOnApplication.objects.all().order_by("id")


class DenialMatchOnApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = denial.DenialMatchOnApplicationViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.DenialMatchOnApplication.objects.all().order_by("id")
