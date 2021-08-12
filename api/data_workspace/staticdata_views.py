from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.control_list_entries.serializers import ControlListEntrySerializer
from api.staticdata.countries.models import Country
from api.staticdata.countries.serializers import CountrySerializer
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.statuses.serializers import CaseStatusSerializer


class ControlListEntriesListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = ControlListEntrySerializer
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
