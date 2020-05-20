from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from static.control_list_entries.helpers import get_control_list_entry
from static.control_list_entries.models import ControlListEntry
from static.control_list_entries.serializers import ControlListEntrySerializerWithLinks


@permission_classes((permissions.AllowAny,))
class ControlListEntriesList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        """
        Returns list of all Control List Entries
        """
        queryset = ControlListEntry.objects.all().prefetch_related("children")

        if request.GET.get("flatten"):
            return JsonResponse(
                data={"control_list_entries": list(queryset.filter(rating__isnull=False).values("rating", "text"))}
            )

        serializer = ControlListEntrySerializerWithLinks(queryset.filter(parent=None), many=True)
        return JsonResponse(data={"control_list_entries": serializer.data})


class ControlListEntryDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, rating):
        """
        Returns details of a specific control ratings
        """
        control_list_entry = get_control_list_entry(rating)
        serializer = ControlListEntrySerializerWithLinks(control_list_entry)
        return JsonResponse(data={"control_list_entry": serializer.data})
