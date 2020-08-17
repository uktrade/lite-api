from django.http import JsonResponse
from rest_framework.views import APIView

from api.core.authentication import SharedAuthentication
from api.static.units.enums import Units


class UnitsList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        unit_choices = dict(Units.choices)
        return JsonResponse(data={"units": unit_choices})
