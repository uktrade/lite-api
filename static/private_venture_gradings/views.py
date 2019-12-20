from django.http import JsonResponse
from rest_framework.views import APIView

from goods.enums import PVGrading
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class PVGradingsList(APIView):
    def get(self, request):
        return JsonResponse(data={"pv-gradings": PVGrading.choices})
