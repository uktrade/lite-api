from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.users import models
from api.users.serializers import BaseUserViewSerializer, GovUserViewSerializer
from api.core.authentication import DataWorkspaceOnlyAuthentication


class BaseUserListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = BaseUserViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.BaseUser.objects.all()


class GovUserListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = GovUserViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GovUser.objects.all()
