from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.status import HTTP_200_OK
from static.statuses.models import CaseStatus
from static.statuses.serializers import CaseStatusSerializer


class StatusesAsList(APIView):
    def get(self, request):
        # Exclude the 'Draft' system status
        statuses = CaseStatus.objects.all().order_by("priority").exclude(status="draft")
        serializer = CaseStatusSerializer(statuses, many=True)
        return JsonResponse(data={"statuses": serializer.data}, status=HTTP_200_OK)


class StatusProperties(APIView):
    def get(self, request, status):
        """ Return is_read_only and is_terminal properties for a case status. """
        status_properties = CaseStatus.objects.filter(status=status).values_list("is_read_only", "is_terminal")[0]
        return JsonResponse(
            data={"is_read_only": status_properties[0], "is_terminal": status_properties[1]}, status=HTTP_200_OK
        )
