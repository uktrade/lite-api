import csv

import openpyxl
from django.http import JsonResponse
from openpyxl.cell import Cell
from rest_framework import permissions, status
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from conf.helpers import convert_queryset_to_str
from static.control_list_entries.helpers import get_rating
from static.control_list_entries.models import ControlRating
from static.control_list_entries.parser import parse_list_into_control_ratings
from static.control_list_entries.serializers import ControlRatingSerializer


@permission_classes((permissions.AllowAny,))
class ControlListEntriesList(APIView):
    """
    List all Control Ratings
    """
    def get(self, request):
        """
        Returns list of all Control Ratings
        """
        if request.GET.get('flatten'):
            return JsonResponse(data={
                'control_ratings': convert_queryset_to_str(ControlRating.objects.values_list('rating', flat=True))
            })

        serializer = ControlRatingSerializer(ControlRating.objects.filter(parent=None), many=True)
        return JsonResponse(data={'control_ratings': serializer.data})

    def post(self, request):
        """
        Add a new control rating
        """

        # Update the parent of the data
        data = request.data
        data['parent'] = None

        serializer = ControlRatingSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'control_rating': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class ControlListEntryDetail(APIView):
    """
    Parse lists
    """
    def get(self, request):
        wb = openpyxl.load_workbook('lite-content/lite-permissions-finder/spreadsheet.xlsx')
        worksheet = wb["UK Military List"]
        parse_list_into_control_ratings(worksheet)

        return JsonResponse(data={'control-ratings': ControlRatingSerializer(ControlRating.objects.all(), many=True).data})


class UploadData(APIView):
    """
    Details of a specific control rating
    """
    def get(self, request, rating):
        """
        Returns details of a specific control ratings
        """
        control_rating = get_rating(rating)
        serializer = ControlRatingSerializer(control_rating)
        return JsonResponse(data={'control_rating': serializer.data})

    def post(self, request, rating):
        """
        Add a new control rating
        """
        control_rating = get_rating(rating)

        # Update the parent of the data
        data = request.data
        data['parent'] = str(control_rating.id)

        serializer = ControlRatingSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'control_rating': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, rating):
        """
        Update a control rating
        """
        control_rating = get_rating(rating)

        serializer = ControlRatingSerializer(instance=control_rating, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'control_rating': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
