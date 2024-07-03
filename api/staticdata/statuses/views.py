from django.http import JsonResponse

from rest_framework.generics import RetrieveAPIView
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from api.cases.views.search.service import get_case_status_list
from api.core.authentication import SharedAuthentication
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.statuses.serializers import CaseStatusPropertiesSerializer


class StatusesAsList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        statuses = get_case_status_list()
        return JsonResponse(data={"statuses": statuses}, status=HTTP_200_OK)


class StatusProperties(RetrieveAPIView):
    authentication_classes = (SharedAuthentication,)
    queryset = CaseStatus.objects.all()
    serializer_class = CaseStatusPropertiesSerializer
    lookup_field = "status"
