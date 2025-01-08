from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from api.audit_trail.models import Audit
from api.audit_trail import service as audit_trail_service
from api.audit_trail.serializers import AuditSerializer
from api.cases.views.search.activity_filters import (
    AuditEventCaseFilter,
    AuditEventExporterUserFilter,
    AuditEventMentionsFilter,
    AuditEventTeamFilter,
)
from api.cases.models import Case
from api.core.authentication import GovAuthentication


class CaseActivityView(ListAPIView):
    authentication_classes = (GovAuthentication,)
    filter_backends = [
        AuditEventCaseFilter,
        AuditEventExporterUserFilter,
        AuditEventMentionsFilter,
        AuditEventTeamFilter,
    ]
    serializer_class = AuditSerializer
    queryset = Audit.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        return JsonResponse(data={"activity": serializer.data}, status=status.HTTP_200_OK)


class CaseActivityFiltersView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        content_type = ContentType.objects.get_for_model(Case)
        filters = audit_trail_service.get_objects_activity_filters(pk, content_type)

        return JsonResponse(data={"filters": filters}, status=status.HTTP_200_OK)
