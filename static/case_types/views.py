from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK

from cases.enums import CaseTypeEnum


class CaseTypes(APIView):
    def get(self, request):
        case_types = {choice[0]: choice[1] for choice in CaseTypeEnum.choices}
        return JsonResponse(data={"case_types": case_types}, status=HTTP_200_OK)
