from rest_framework import generics

from api.core.authentication import ExporterAuthentication
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.exporter.control_list_entries.serializers import ControlListEntriesListSerializer


class ControlListEntriesList(generics.ListAPIView):
    authentication_classes = (ExporterAuthentication,)
    pagination_class = None
    serializer_class = ControlListEntriesListSerializer

    def get_queryset(self):
        include_deprecated = self.request.GET.get("include_deprecated", False)
        if include_deprecated:
            return ControlListEntry.objects.filter(controlled=True)

        return ControlListEntry.objects.filter(controlled=True, deprecated=False)
