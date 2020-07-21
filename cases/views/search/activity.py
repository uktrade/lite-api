from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.serializers import AuditSerializer
from cases.models import Case
from conf.authentication import GovAuthentication
from users.models import GovNotification


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
        GovNotification.objects.filter(user=request.user, object_id__in=[obj["id"] for obj in data]).delete()

        return JsonResponse(data={"activity": data}, status=status.HTTP_200_OK)


class CaseActivityFiltersView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        content_type = ContentType.objects.get_for_model(Case)
        filters = audit_trail_service.get_objects_activity_filters(pk, content_type)

        return JsonResponse(data={"filters": filters}, status=status.HTTP_200_OK)
