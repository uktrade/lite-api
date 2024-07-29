from rest_framework import viewsets

from api.applications.models import StandardApplication
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v2.serializers import ApplicationSerializer


class ApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    queryset = StandardApplication.objects.filter(amendment__isnull=True).exclude(submitted_at__isnull=True)
    serializer_class = ApplicationSerializer
