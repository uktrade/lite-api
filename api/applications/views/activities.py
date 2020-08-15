from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from api.audit_trail import service as audit_trail_service
from api.audit_trail.serializers import AuditSerializer
from cases.libraries.get_case import get_case
from api.conf.authentication import ExporterAuthentication


class ActivityView(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        case = get_case(pk)
        audit_trail_qs = audit_trail_service.get_activity_for_user_and_model(user=request.user, object_type=case)

        return JsonResponse(
            data={"activity": AuditSerializer(audit_trail_qs, many=True).data}, status=status.HTTP_200_OK
        )
