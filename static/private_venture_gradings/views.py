from django.http import JsonResponse
from rest_framework.views import APIView

from api.conf.authentication import SharedAuthentication
from goods.enums import PvGrading


class PVGradingsList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        return JsonResponse(data={"pv_gradings": [{choice[0]: choice[1]} for choice in PvGrading.choices]})


class GovPVGradingsList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        return JsonResponse(data={"pv_gradings": [{choice[0]: choice[1]} for choice in PvGrading.gov_choices]})
