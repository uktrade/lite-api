from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.core.authentication import ExporterAuthentication, SharedAuthentication
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.parties.enums import PartyType
from api.queries.end_user_advisories.libraries.get_end_user_advisory import get_end_user_advisory_by_pk
from api.queries.end_user_advisories.models import EndUserAdvisoryQuery
from api.queries.end_user_advisories.serializers import EndUserAdvisoryViewSerializer, EndUserAdvisoryListSerializer
from api.users.libraries.notifications import get_case_notifications
from lite_routing.routing_rules_internal.flagging_engine import apply_flagging_rules_to_case


class EndUserAdvisoriesList(ListAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = EndUserAdvisoryListSerializer

    def get_queryset(self):
        name = self.request.GET.get("name")
        queryset = EndUserAdvisoryQuery.objects.filter(
            organisation_id=get_request_user_organisation_id(self.request)
        ).select_related("end_user", "end_user__country")

        if name:
            queryset = queryset.filter(end_user__name__icontains=name)

        return queryset

    def get_paginated_response(self, data):
        data = get_case_notifications(data, self.request)
        return super().get_paginated_response(data)

    def post(self, request):
        """
        Create a new End User Advisory Enquiry query case instance
        """
        data = JSONParser().parse(request)
        if not data.get("end_user"):
            data["end_user"] = {}
        organisation_id = get_request_user_organisation_id(request)
        data["organisation"] = organisation_id
        data["end_user"]["organisation"] = organisation_id
        data["end_user"]["type"] = PartyType.END_USER
        data["submitted_by"] = request.user

        serializer = EndUserAdvisoryViewSerializer(data=data)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if "validate_only" not in data or data["validate_only"] == "False":
            eua = serializer.save()
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.CREATED,
                action_object=eua.get_case(),
                payload={"status": {"new": eua.status.status}},
            )
            apply_flagging_rules_to_case(eua)
            return JsonResponse(data={"end_user_advisory": serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return JsonResponse(data={}, status=status.HTTP_200_OK)


class EndUserAdvisoryDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        """
        View a single end user advisory's details
        """
        end_user_advisory = get_end_user_advisory_by_pk(pk)
        case_id = end_user_advisory.id

        serializer = EndUserAdvisoryViewSerializer(
            end_user_advisory,
            context={
                "exporter_user": request.user.exporteruser,
                "organisation_id": get_request_user_organisation_id(request),
            },
        )
        return JsonResponse(data={"end_user_advisory": serializer.data, "case_id": case_id}, status=status.HTTP_200_OK)
