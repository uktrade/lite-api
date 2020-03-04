from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK

from static.decisions.enums import DecisionsEnum as DecisionsEnum


class Decisions(APIView):
    def get(self, request):
        return JsonResponse(data={"decisions": DecisionsEnum.to_representation()}, status=HTTP_200_OK)
