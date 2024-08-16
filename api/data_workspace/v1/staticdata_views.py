from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.control_list_entries.serializers import ControlListEntriesListSerializer
from api.staticdata.regimes.models import Regime, RegimeSubsection, RegimeEntry
from api.staticdata.regimes.serializers import (
    RegimesListSerializer,
    RegimeSubsectionsListSerializer,
    RegimeEntriesListSerializer,
)
from api.staticdata.countries.models import Country
from api.staticdata.countries.serializers import CountrySerializer
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.statuses.serializers import CaseStatusSerializer


class ControlListEntriesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = ControlListEntriesListSerializer
    pagination_class = LimitOffsetPagination
    queryset = ControlListEntry.objects.all()


class CountriesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = CountrySerializer
    pagination_class = LimitOffsetPagination
    queryset = Country.objects.all()


class CaseStatusListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = CaseStatusSerializer
    pagination_class = LimitOffsetPagination
    queryset = CaseStatus.objects.all()


class RegimesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = RegimesListSerializer
    pagination_class = LimitOffsetPagination
    queryset = Regime.objects.all()


class RegimeSubsectionsListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = RegimeSubsectionsListSerializer
    pagination_class = LimitOffsetPagination
    queryset = RegimeSubsection.objects.all()


class RegimeEntriesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = RegimeEntriesListSerializer
    pagination_class = LimitOffsetPagination
    queryset = RegimeEntry.objects.all()
