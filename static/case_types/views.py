from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK

from cases.enums import CaseTypeEnum


class CaseTypes(APIView):
    def get(self, request):
        return JsonResponse(data={"case_types": CaseTypeEnum.case_types_to_representation()}, status=HTTP_200_OK)
