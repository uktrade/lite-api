from rest_framework import viewsets

from api.applications.models import StandardApplication
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import EcjuQuery
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v2.serializers import (
    ApplicationSerializer,
    RFISerializer,
    StatusChangeSerializer,
)


class ApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = StandardApplication.objects.filter(amendment__isnull=True).exclude(submitted_at__isnull=True)
    serializer_class = ApplicationSerializer


class StatusChangeListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = Audit.objects.filter(verb=AuditType.UPDATED_STATUS).order_by("created_at")
    serializer_class = StatusChangeSerializer


class RFIListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = EcjuQuery.objects.all()
    serializer_class = RFISerializer
