from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v1.serializers import LicenceWithoutGoodsSerializer
from api.licences import models
from api.licences.serializers import view_licence as serializers


class GoodOnLicenceList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = serializers.GoodOnLicenceReportsViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GoodOnLicence.objects.all()


class LicencesList(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = LicenceWithoutGoodsSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.Licence.objects.all()
