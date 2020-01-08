import json

from django.http import JsonResponse
from rest_framework import status, serializers
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.libraries.application_helpers import can_status_can_be_set_by_gov_user
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from conf import constants
from conf.authentication import ExporterAuthentication, SharedAuthentication
from conf.permissions import assert_user_has_permission
from queries.end_user_advisories.libraries.get_end_user_advisory import get_end_user_advisory_by_pk
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from queries.end_user_advisories.serializers import EndUserAdvisoryListSerializer, EndUserAdvisoryViewSerializer
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class EndUserAdvisoriesList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        View all end user advisories belonging to an organisation.
        """
        end_user_advisories = EndUserAdvisoryQuery.objects.filter(organisation=request.user.organisation)
        serializer = EndUserAdvisoryListSerializer(
            end_user_advisories, many=True, context={"exporter_user": request.user}
        )
        return JsonResponse(data={"end_user_advisories": serializer.data})

    def post(self, request):
        """
        Create a new End User Advisory Enquiry query case instance
        """
        data = JSONParser().parse(request)

        if not data.get("end_user"):
            data["end_user"] = {}

        data["organisation"] = request.user.organisation.id
        data["end_user"]["organisation"] = request.user.organisation.id

        serializer = EndUserAdvisoryListSerializer(data=data)

        try:
            if serializer.is_valid():
                if "validate_only" not in data or data["validate_only"] == "False":
                    serializer.save()
                    return JsonResponse(data={"end_user_advisory": serializer.data}, status=status.HTTP_201_CREATED)
                else:
                    return JsonResponse(data={}, status=status.HTTP_200_OK)

            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except serializers.ValidationError as e:
            return JsonResponse(data={"errors": e}, status=status.HTTP_400_BAD_REQUEST)


class EndUserAdvisoryDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, pk):
        """
        View a single end user advisory's details
        """
        end_user_advisory = get_end_user_advisory_by_pk(pk)
        case_id = end_user_advisory.id

        serializer = EndUserAdvisoryViewSerializer(end_user_advisory, context={"exporter_user": request.user})
        return JsonResponse(data={"end_user_advisory": serializer.data, "case_id": case_id}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """
        Update an end user advisory instance.
        """
        end_user_advisory = get_end_user_advisory_by_pk(pk)

        data = json.loads(request.body)

        # Only allow the final decision if the user has the MANAGE_FINAL_ADVICE permission
        if data.get("status") == CaseStatusEnum.FINALISED:
            assert_user_has_permission(request.user, constants.GovPermissions.MANAGE_FINAL_ADVICE)

        new_status = data.get("status")
        if not can_status_can_be_set_by_gov_user(request.user, end_user_advisory.status.status, new_status):
            return JsonResponse(
                data={"errors": ["Status cannot be set by Gov user."]}, status=status.HTTP_400_BAD_REQUEST
            )

        request.data["status"] = get_case_status_by_status(data.get("status"))

        serializer = EndUserAdvisoryViewSerializer(end_user_advisory, data=request.data, partial=True)

        if serializer.is_valid():
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.UPDATED_STATUS,
                target=end_user_advisory.get_case(),
                payload={"status": data.get("status")},
            )
            serializer.update(end_user_advisory, request.data)
            return JsonResponse(data={"end_user_advisory": serializer.data})
        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
