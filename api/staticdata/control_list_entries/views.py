from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from api.core.authentication import GovAuthentication, SharedAuthentication
from api.staticdata.control_list_entries.helpers import get_control_list_entry, convert_control_list_entries_to_tree
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.control_list_entries.serializers import ControlListEntrySerializerWithLinks


@permission_classes((permissions.AllowAny,))
class ControlListEntriesList(APIView):
    authentication_classes = (GovAuthentication,)

    def get_queryset(self, include_unselectable=False):
        if include_unselectable:
            return ControlListEntry.objects.filter(controlled=True)

        return ControlListEntry.objects.filter(controlled=True, selectable_for_assessment=True)

    def get(self, request):
        """
        Returns list of all Control List Entries
        """

        include_unselectable = request.GET.get("include_unselectable", False)

        queryset = self.get_queryset(include_unselectable=include_unselectable)

        if request.GET.get("group", False):
            return JsonResponse(data={"control_list_entries": convert_control_list_entries_to_tree(queryset.values())})

        if request.GET.get("include_parent", False):
            return JsonResponse(data={"control_list_entries": list(queryset.values("rating", "text", "parent"))})

        return JsonResponse(data={"control_list_entries": list(queryset.values("rating", "text"))})


class ControlListEntryDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, rating):
        """
        Returns details of a specific control ratings
        """
        control_list_entry = get_control_list_entry(rating)
        serializer = ControlListEntrySerializerWithLinks(control_list_entry)
        return JsonResponse(data={"control_list_entry": serializer.data})
