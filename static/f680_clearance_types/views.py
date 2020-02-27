from django.http import JsonResponse
from rest_framework.views import APIView

from static.f680_clearance_types.enums import F680ClearanceTypeEnum
from static.f680_clearance_types.models import F680ClearanceType


class F680ClearanceTypesView(APIView):
    def get(self, request):
        clearance_types = {key: value for key, value in F680ClearanceTypeEnum.choices}
        return JsonResponse(data={"f680_clearance_types": clearance_types})
