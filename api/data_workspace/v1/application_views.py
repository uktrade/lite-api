from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.applications import models
from api.applications.serializers import standard_application, good, party, denial
from api.core.authentication import DataWorkspaceOnlyAuthentication


class StandardApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = standard_application.StandardApplicationDataWorkspaceSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.StandardApplication.objects.all()


class GoodOnApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = good.GoodOnApplicationDataWorkspaceSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GoodOnApplication.objects.all()


class GoodOnApplicationControlListEntriesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = good.GoodOnApplicationControlListEntrySerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GoodOnApplicationControlListEntry.objects.all()


class GoodOnApplicationRegimeEntriesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = good.GoodOnApplicationRegimeEntrySerializer
    pagination_class = LimitOffsetPagination
    queryset = models.GoodOnApplicationRegimeEntry.objects.all()


class PartyOnApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = party.PartyOnApplicationViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.PartyOnApplication.objects.all().order_by("id")


class DenialMatchOnApplicationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = denial.DenialMatchOnApplicationViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = models.DenialMatchOnApplication.objects.all().order_by("id")
