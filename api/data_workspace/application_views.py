from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.applications import models
from api.applications.serializers import standard_application, good, party
from api.core.authentication import DataWorkspaceOnlyAuthentication


class StandardApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = standard_application.StandardApplicationViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.StandardApplication.objects.all()


class GoodOnApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = good.GoodOnApplicationViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GoodOnApplication.objects.all()


class GoodOnApplicationControlListEntriesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = good.GoodOnApplicationControlListEntrySerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GoodOnApplicationControlListEntry.objects.all()


class PartyOnApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = party.PartyOnApplicationViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.PartyOnApplication.objects.all()
