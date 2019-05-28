from django.http import JsonResponse
from rest_framework.views import APIView

from static.units.units import Units


class UnitsList(APIView):
    def get(self, request):
        unit_choices = {key: str(value) for key, value in Units.__dict__.items()
                        if not key.startswith('_') and not callable(key)}
        return JsonResponse(data={'units': unit_choices}, safe=False)
