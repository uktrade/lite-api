from rest_framework import generics

from api.core.authentication import GovAuthentication
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.caseworker.control_list_entries.serializers import ControlListEntriesListSerializer


class ControlListEntriesList(generics.ListAPIView):
    authentication_classes = (GovAuthentication,)
    pagination_class = None
    serializer_class = ControlListEntriesListSerializer

    def get_queryset(self):
        include_unselectable = self.request.GET.get("include_non_selectable_for_assessment", False)
        if include_unselectable:
            return ControlListEntry.objects.filter(controlled=True)

        return ControlListEntry.objects.filter(controlled=True, selectable_for_assessment=True)
