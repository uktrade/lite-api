from django.http import JsonResponse
from rest_framework.views import APIView

from goods.enums import PvGrading


class PVGradingsList(APIView):
    def get(self, request):
        return JsonResponse(data={"pv_gradings": [{choice[0]: choice[1]} for choice in PvGrading.choices]})
