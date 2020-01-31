from django.http import JsonResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from cases.views.search.service import get_case_status_list
from static.statuses.models import CaseStatus


class StatusesAsList(APIView):
    def get(self, request):
        statuses = get_case_status_list()
        return JsonResponse(data={"statuses": statuses}, status=HTTP_200_OK)


class StatusProperties(APIView):
    def get(self, request, status):
        """ Return is_read_only and is_terminal properties for a case status. """
        status_properties = CaseStatus.objects.filter(status=status).values_list("is_read_only", "is_terminal")[0]
        return JsonResponse(
            data={"is_read_only": status_properties[0], "is_terminal": status_properties[1]}, status=HTTP_200_OK
        )
