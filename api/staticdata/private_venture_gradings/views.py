from django.http import JsonResponse
from rest_framework.views import APIView

from api.core.authentication import SharedAuthentication
from api.goods.enums import PvGrading


class PVGradingsList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        return JsonResponse(data={"pv_gradings": [{choice[0]: choice[1]} for choice in PvGrading.choices]})


class PVGradingsUpdatedList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        return JsonResponse(data={"pv_gradings": [{choice[0]: choice[1]} for choice in PvGrading.choices_new]})


class GovPVGradingsList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        return JsonResponse(data={"pv_gradings": [{choice[0]: choice[1]} for choice in PvGrading.gov_choices]})
