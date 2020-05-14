from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK

from cases.enums import CaseTypeEnum
from cases.models import CaseType
from cases.serializers import CaseTypeSerializer
from conf.authentication import SharedAuthentication
from conf.helpers import str_to_bool


class CaseTypes(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        type_only = request.GET.get("type_only", "True")

        # If type_only is True, return only the case_type_reference key-value pairs
        if str_to_bool(type_only):
            case_types = CaseTypeEnum.case_types_to_representation()
        else:
            case_types = CaseTypeSerializer(CaseType.objects.all(), many=True).data

        return JsonResponse(data={"case_types": case_types}, status=HTTP_200_OK)
