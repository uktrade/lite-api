from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.goods import models, serializers
from api.core.authentication import DataWorkspaceOnlyAuthentication


class GoodListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = serializers.GoodSerializerInternal
    pagination_class = LimitOffsetPagination
    queryset = models.Good.objects.all()
