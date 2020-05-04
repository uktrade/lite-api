import datetime

from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from audit_trail.serializers import AuditSerializer
from cases.libraries.delete_notifications import delete_gov_user_notifications
from conf.authentication import GovAuthentication
from users.enums import UserType
from users.models import GovUser, GovNotification


class CaseActivityView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        data = request.GET

        def make_date(prefix, data):
            """
            Makes date from Lite forms DateInput data.
            """
            try:
                return datetime.date(
                    day=int(data.get(f"{prefix}_day")),
                    month=int(data.get(f"{prefix}_month")),
                    year=int(data.get(f"{prefix}_year")),
                )
            except (TypeError, ValueError):
                # Handle gracefully if no date or incorrect date data passed
                pass

        user_id = data.get("user_id")
        team_id = data.get("team_id")
        user_type = UserType(data["user_type"]) if data.get("user_type") else None
        audit_type = AuditType(data["activity_type"]) if data.get("activity_type") else None
        date_from = make_date("from", data)
        date_to = make_date("to", data)
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

        data = AuditSerializer(audit_trail_qs, many=True).data

        if isinstance(request.user, GovUser):
            # Delete notifications relatedto audits
            GovNotification.objects.filter(user=request.user, object_id__in=[obj["id"] for obj in data]).delete()

        return JsonResponse(data={"activity": data}, status=status.HTTP_200_OK)


class CaseActivityFiltersView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        filters = audit_trail_service.get_case_activity_filters(pk)

        return JsonResponse(data={"filters": filters}, status=status.HTTP_200_OK)
