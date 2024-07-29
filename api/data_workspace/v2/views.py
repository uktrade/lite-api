from rest_framework import viewsets

from api.applications.models import StandardApplication
from api.cases.models import EcjuQuery
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v2.serializers import (
    ApplicationSerializer,
    RFISerializer,
)


class ApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = StandardApplication.objects.filter(amendment__isnull=True).exclude(submitted_at__isnull=True)
    serializer_class = ApplicationSerializer


class RFIListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = EcjuQuery.objects.all()
    serializer_class = RFISerializer
