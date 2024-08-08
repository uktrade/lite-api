from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.goods import models, serializers
from api.core.authentication import DataWorkspaceOnlyAuthentication


class GoodListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = serializers.GoodSerializerInternalIncludingPrecedents
    pagination_class = LimitOffsetPagination
    queryset = models.Good.objects.all()


class GoodControlListEntryListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = serializers.GoodControlListEntryViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GoodControlListEntry.objects.all()
