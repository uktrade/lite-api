from django.http import JsonResponse
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from cases.libraries.get_case import get_case
from conf.authentication import GovAuthentication


class Activity(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Retrieves all activity related to a case
    * Case Updates
    * Case Notes
    * ECJU Queries
    """

    def get(self, request, pk):
        case = get_case(pk)
        audit_trail = audit_trail_service.get_obj_trail(case)

        return JsonResponse(data={"activity": audit_trail})
