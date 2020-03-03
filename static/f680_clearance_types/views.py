from django.http import JsonResponse
from rest_framework.views import APIView

from static.f680_clearance_types.enums import F680ClearanceTypeEnum


class F680ClearanceTypesView(APIView):
    def get(self, request):
        clearance_types = {key: value for key, value in F680ClearanceTypeEnum.choices}
        return JsonResponse(data={"types": clearance_types})
