from django.http import JsonResponse
from rest_framework.views import APIView

from static.units.enums import Units


class UnitsList(APIView):
    def get(self, request):
        unit_choices = dict(Units.choices)
        return JsonResponse(data={'units': unit_choices})
