from django.http import JsonResponse
from rest_framework.views import APIView

from api.conf.authentication import SharedAuthentication
from api.staticdata.units.enums import Units


class UnitsList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        unit_choices = dict(Units.choices)
        return JsonResponse(data={"units": unit_choices})
