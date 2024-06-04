from copy import deepcopy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView

from api.applications.libraries.case_status_helpers import get_case_statuses
from api.applications.models import BaseApplication, DenialMatchOnApplication
from api.applications.serializers import denial
from api.core.authentication import GovAuthentication
from lite_content.lite_api import strings


class ApplicationDenialMatchesOnApplication(APIView):
    """
    Denial matches belonging to a standard application
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        denial_matches = DenialMatchOnApplication.objects.filter(
            application_id=pk, denial_entity__denial__is_revoked=False
        )
        denial_matches_data = denial.DenialMatchOnApplicationViewSerializer(denial_matches, many=True).data
        return JsonResponse(data={"denial_matches": denial_matches_data})

    def post(self, request, pk):
        data = deepcopy(request.data)

        # This is for backward compatablity to be remove once FE has been updated.
        for denial_match_item in data:
            if denial_match_item.get("denial"):
                denial_match_item["denial_entity"] = denial_match_item.pop("denial")
        serializer = denial.DenialMatchOnApplicationCreateSerializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            return_data = serializer.data
            # This is for backward compatablity to be remove once FE has been updated.
            for return_item in return_data:
                return_item.update({"denial": return_item["denial_entity"]})
            return JsonResponse(data={"denial_matches": return_data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        application = get_object_or_404(BaseApplication.objects.all(), pk=pk)

        if application.status.status in get_case_statuses(read_only=True):
            return JsonResponse(
                data={"errors": [strings.Applications.Generic.READ_ONLY]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for obj in DenialMatchOnApplication.objects.filter(id__in=request.data.get("objects", [])):
            obj.delete()

        return JsonResponse(data={"status": "success"}, status=status.HTTP_200_OK)
