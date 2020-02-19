from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK

from cases.enums import CaseTypeEnum
from cases.models import CaseType
from cases.serializers import CaseTypeSerializer
from conf.helpers import str_to_bool


class CaseTypes(APIView):
    def get(self, request):
        type_only = request.GET.get("type_only", "True")

        if str_to_bool(type_only):
            case_types = CaseTypeEnum.case_types_to_representation()
        else:
            case_types = CaseTypeSerializer(CaseType.objects.all(), many=True).data

        return JsonResponse(data={"case_types": case_types}, status=HTTP_200_OK)
