from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK

from cases.enums import AdviceType as AdviceType


class Decisions(APIView):
    def get(self, request):
        return JsonResponse(data={"decisions": AdviceType.to_representation()}, status=HTTP_200_OK)
