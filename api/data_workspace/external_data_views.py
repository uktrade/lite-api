from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.external_data import models
from api.external_data.serializers import DenialSerializer
from api.core.authentication import DataWorkspaceOnlyAuthentication


class ExternalDataDenialView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = DenialSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.Denial.objects.all()
