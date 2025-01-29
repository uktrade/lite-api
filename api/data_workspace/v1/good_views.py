from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.conf.pagination import CreatedAtCursorPagination
from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.data_workspace.v1.serializers import GoodSerializer
from api.goods.models import (
    Good,
    GoodControlListEntry,
)
from api.goods.serializers import GoodControlListEntryViewSerializer


class GoodListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = GoodSerializer
    pagination_class = CreatedAtCursorPagination
    queryset = Good.objects.prefetch_related("control_list_entries")


class GoodControlListEntryListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = GoodControlListEntryViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = GoodControlListEntry.objects.all()
