from rest_framework.views import APIView

from conf.serializers import response_serializer
from static.statuses.models import CaseStatus
from static.statuses.serializers import CaseStatusSerializer


class StatusesAsList(APIView):
    def get(self, request):
        statuses = CaseStatus.objects.all().order_by('priority')
        return response_serializer(CaseStatusSerializer, obj=statuses, many=True, response_name='statuses')
