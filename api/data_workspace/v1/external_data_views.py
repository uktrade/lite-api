from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.external_data import models
from api.external_data.serializers import DenialEntitySerializer
from api.core.authentication import DataWorkspaceOnlyAuthentication


class ExternalDataDenialView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = DenialEntitySerializer
    pagination_class = LimitOffsetPagination
    queryset = models.DenialEntity.objects.all().order_by("id")
