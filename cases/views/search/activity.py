from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.serializers import AuditSerializer
from cases.libraries.delete_notifications import delete_gov_user_notifications
from cases.models import Case
from api.conf.authentication import GovAuthentication
from api.users.models import GovUser


class CaseActivityView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        filter_data = audit_trail_service.get_filters(request.GET)
        content_type = ContentType.objects.get_for_model(Case)
        audit_trail_qs = audit_trail_service.filter_object_activity(
            object_id=pk, object_content_type=content_type, **filter_data
        )

        data = AuditSerializer(audit_trail_qs, many=True).data

        # Delete notifications related to audits
        if isinstance(request.user, GovUser):
            delete_gov_user_notifications(request.user, [obj["id"] for obj in data])

        return JsonResponse(data={"activity": data}, status=status.HTTP_200_OK)


class CaseActivityFiltersView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        content_type = ContentType.objects.get_for_model(Case)
        filters = audit_trail_service.get_objects_activity_filters(pk, content_type)

        return JsonResponse(data={"filters": filters}, status=status.HTTP_200_OK)
