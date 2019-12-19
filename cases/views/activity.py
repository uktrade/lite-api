from django.http import JsonResponse
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.serializers import AuditSerializer
from cases.libraries.get_case import get_case
from conf.authentication import SharedAuthentication


class Activity(APIView):
    authentication_classes = (SharedAuthentication,)
    """
    Retrieves all activity related to a case
    * Case Updates
    * Case Notes
    * ECJU Queries
    """

    def get(self, request, pk):
        case = get_case(pk)
        audit_trail_qs = audit_trail_service.get_user_obj_trail_qs(user=request.user, obj=case)

        return JsonResponse(data={"activity": AuditSerializer(audit_trail_qs, many=True).data})
