from django.http import JsonResponse
from rest_framework.views import APIView

from static.statuses.models import CaseStatus
from static.statuses.serializers import CaseStatusSerializer


class StatusesAsList(APIView):
    def get(self, request):
        statuses = CaseStatus.objects.all().order_by('priority')
        serializer = CaseStatusSerializer(statuses, many=True)
        return JsonResponse(data={'statuses': serializer.data})
