from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from static.control_list_entries.helpers import get_control_list_entry
from static.control_list_entries.models import ControlListEntry
from static.control_list_entries.serializers import ControlListEntrySerializer


@permission_classes((permissions.AllowAny,))
class ControlListEntriesList(APIView):
    """
    List all Control Ratings
    """

    def get(self, request):
        """
        Returns list of all Control List Entries
        """
        if request.GET.get('flatten'):
            return JsonResponse(data={'control_list_entries': list(ControlListEntry.objects
                                                                   .filter(is_decontrolled=False, rating__isnull=False)
                                                                   .values('rating', 'text'))})

        serializer = ControlListEntrySerializer(ControlListEntry.objects.filter(parent=None), many=True)
        return JsonResponse(data={'control_list_entries': serializer.data})


class ControlListEntryDetail(APIView):
    """
    Details of a specific control list entry
    """

    def get(self, request, rating):
        """
        Returns details of a specific control ratings
        """
        control_list_entry = get_control_list_entry(rating)
        serializer = ControlListEntrySerializer(control_list_entry)
        return JsonResponse(data={'control_list_entry': serializer.data})
