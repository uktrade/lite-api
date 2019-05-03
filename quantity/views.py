import json

from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from quantity.units import Units


class UnitsList(APIView):

    def get(self, request):

        unit_choices = {key: str(value) for key, value in Units.__dict__.items()
                        if not key.startswith('_') and not callable(key)}
        return JsonResponse(data=unit_choices,
                            status=status.HTTP_200_OK, safe=False)
