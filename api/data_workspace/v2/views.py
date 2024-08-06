from rest_framework import viewsets
from rest_framework.response import Response

from api.applications.models import StandardApplication
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import EcjuQuery
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v2.serializers import (
    ApplicationSerializer,
    RFISerializer,
    StatusSerializer,
    StatusChangeSerializer,
)
from api.staticdata.statuses.enums import CaseStatusEnum


class ApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = StandardApplication.objects.filter(amendment__isnull=True).exclude(submitted_at__isnull=True)
    serializer_class = ApplicationSerializer


class StatusListView(viewsets.ViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)

    def list(self, request):
        statuses = [status for status in CaseStatusEnum.all()]
        return Response(StatusSerializer(statuses, many=True).data)


class StatusChangeListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = Audit.objects.filter(verb=AuditType.UPDATED_STATUS).order_by("created_at")
    serializer_class = StatusChangeSerializer


class RFIListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = EcjuQuery.objects.all()
    serializer_class = RFISerializer
