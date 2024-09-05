from rest_framework import generics

from api.core.authentication import ExporterAuthentication
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.exporter.control_list_entries.serializers import ControlListEntriesListSerializer


class ControlListEntriesList(generics.ListAPIView):
    authentication_classes = (ExporterAuthentication,)
    pagination_class = None
    serializer_class = ControlListEntriesListSerializer
    queryset = ControlListEntry.objects.filter(controlled=True, deprecated=False)
