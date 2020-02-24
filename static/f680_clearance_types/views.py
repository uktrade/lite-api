from django.http import JsonResponse
from rest_framework.views import APIView

from static.f680_clearance_types.models import F680ClearanceType
from static.f680_clearance_types.serializers import F680ClearanceTypeSerializer


class F680ClearanceTypesView(APIView):
    def get(self, request):
        f680_clearance_types = F680ClearanceType.objects.all()
        serializer = F680ClearanceTypeSerializer(f680_clearance_types, many=True)
        return JsonResponse(data={"f680_clearance_types_temp": serializer.data})
