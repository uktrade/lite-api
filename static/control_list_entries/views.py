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

    def post(self, request):
        """
        Add a new control list entry
        """

        # Update the parent of the data
        data = request.data
        data['parent'] = None

        serializer = ControlListEntrySerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'control_list_entry': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


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

    def post(self, request, rating):
        """
        Add a new control rating
        """
        control_list_entry = get_control_list_entry(rating)

        # Update the parent of the data
        data = request.data
        data['parent'] = str(control_list_entry.id)

        serializer = ControlListEntrySerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'control_list_entry': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, rating):
        """
        Update a control rating
        """
        control_list_entry = get_control_list_entry(rating)

        serializer = ControlListEntrySerializer(instance=control_list_entry, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'control_list_entry': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
