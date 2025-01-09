from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from api.audit_trail.enums import AuditType
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

    def get_queryset(self):
        queryset = Audit.objects.all()
        case_activity_qs = AuditEventCaseFilter().filter_queryset(self.request, queryset, self)
        filtered_qs = AuditEventTeamFilter().filter_queryset(self.request, case_activity_qs, self)
        filtered_qs = AuditEventExporterUserFilter().filter_queryset(self.request, filtered_qs, self)
        filtered_qs = AuditEventMentionsFilter().filter_queryset(self.request, filtered_qs, self)

        return filtered_qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        serializer = self.get_serializer(queryset, many=True)
        print(audit_trail_service.get_filters(request.GET))
        print(queryset.count())
        # breakpoint()
        return JsonResponse(data={"activity": serializer.data}, status=status.HTTP_200_OK)


# class CaseActivityView(APIView):
#     authentication_classes = (GovAuthentication,)

#     def get(self, request, pk):
#         filter_data = audit_trail_service.get_filters(request.GET)
#         content_type = ContentType.objects.get_for_model(Case)
#         audit_trail_qs = audit_trail_service.filter_object_activity(
#             object_id=pk, object_content_type=content_type, **filter_data
#         )
#         case = Case.objects.get(pk=pk)
#         bulk_approval_events = [
#             event
#             for event in Audit.objects.filter(verb=AuditType.CREATE_BULK_APPROVAL_RECOMMENDATION)
#             if case.reference_code in event.payload["case_references"]
#         ]
#         if filter_data["team"]:
#             bulk_approval_events = [
#                 event for event in bulk_approval_events if event.payload.get("team_id") == filter_data["team"]
#             ]
#         bulk_approval_qs = Audit.objects.filter(id__in=[event.id for event in bulk_approval_events])

#         audit_trail_qs = audit_trail_qs | bulk_approval_qs

#         data = AuditSerializer(audit_trail_qs, many=True).data

#         return JsonResponse(data={"activity": data}, status=status.HTTP_200_OK)


class CaseActivityFiltersView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        content_type = ContentType.objects.get_for_model(Case)
        filters = audit_trail_service.get_objects_activity_filters(pk, content_type)

        return JsonResponse(data={"filters": filters}, status=status.HTTP_200_OK)
