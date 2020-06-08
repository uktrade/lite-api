from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from static.control_list_entries.helpers import get_control_list_entry, convert_control_list_entries_to_tree
from static.control_list_entries.serializers import ControlListEntrySerializerWithLinks
from static.control_list_entries.service import control_list_entries_list


@permission_classes((permissions.AllowAny,))
class ControlListEntriesList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        """
        Returns list of all Control List Entries
        """
        control_list_entries = control_list_entries_list()

        if request.GET.get("group", False):
            return JsonResponse(data={"control_list_entries": convert_control_list_entries_to_tree(control_list_entries)})

        return JsonResponse(data={"control_list_entries": [{"rating": entry["rating"], "text": entry["text"]} for entry in control_list_entries]})


class ControlListEntryDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, rating):
        """
        Returns details of a specific control ratings
        """
        control_list_entry = get_control_list_entry(rating)
        serializer = ControlListEntrySerializerWithLinks(control_list_entry)
        return JsonResponse(data={"control_list_entry": serializer.data})
