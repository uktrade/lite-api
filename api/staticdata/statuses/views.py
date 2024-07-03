from django.http import JsonResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from api.cases.views.search.service import get_case_status_list
from api.core.authentication import SharedAuthentication
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus


class StatusesAsList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        statuses = get_case_status_list()
        return JsonResponse(data={"statuses": statuses}, status=HTTP_200_OK)


class StatusProperties(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, status):
        """Return is_read_only and is_terminal properties for a case status."""
        case_status = CaseStatus.objects.get(status=status)
        return JsonResponse(
            data={
                "is_read_only": case_status.is_read_only,
                "is_terminal": case_status.is_terminal,
            },
            status=HTTP_200_OK,
        )
