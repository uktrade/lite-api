from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from audit_trail.serializers import AuditSerializer
from conf.authentication import GovAuthentication
from users.enums import UserType


class SearchCaseActivity(APIView):
    authentication_classes = GovAuthentication,

    def get(self, request, pk):
        data = request.data

        user_id = data.get("user_id")
        team_id = data.get("team_id")
        user_type = UserType(data["user_type"]) if data.get("user_type") else None
        audit_type = AuditType(data["audit_type"]) if data.get("audit_type") else None
        date_from = data.get("date_from")
        date_to = data.get("date_to")
        note_type = data.get("note_type")

        audit_trail_qs = audit_trail_service.filter_case_activity(
            case_id=pk,
            user_id=user_id,
            team=team_id,
            user_type=user_type,
            audit_type=audit_type,
            date_from=date_from,
            date_to=date_to,
            note_type=note_type,
        )

        return JsonResponse(
            data={"activity": AuditSerializer(audit_trail_qs, many=True).data}, status=status.HTTP_200_OK
        )
