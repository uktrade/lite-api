from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework.generics import UpdateAPIView, RetrieveAPIView
from rest_framework.status import HTTP_208_ALREADY_REPORTED

from api.core.authentication import HMRCIntegrationOnlyAuthentication
from api.licences.libraries import hmrc_integration_operations
from api.licences.libraries.hmrc_integration_operations import (
    validate_licence_usage_updates,
    save_licence_usage_updates,
)
from api.licences.models import HMRCIntegrationUsageData, Licence
from api.licences.serializers.hmrc_integration import HMRCIntegrationUsageDataLicencesSerializer


@api_view(["GET", "POST"])
@authentication_classes([HMRCIntegrationOnlyAuthentication])
def mark_emails_as_processed(request):
    """Mark emails at LITE-HMRC as already processed so they won't be processed further by mail task

    This is used mainly as a workaround in certain cases in testing when in setup we want
    process only an individual email so we mark everything as already processed prior to that.
    """
    hmrc_integration_operations.mark_emails_as_processed()
    return Response(status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@authentication_classes([HMRCIntegrationOnlyAuthentication])
def force_mail_push(request):
    """Cascade push of mail by task manager at LITE-HMRC"""
    hmrc_integration_operations.force_mail_push()
    return Response(status=status.HTTP_200_OK)


class HMRCIntegrationRetrieveView(RetrieveAPIView):
    authentication_classes = (HMRCIntegrationOnlyAuthentication,)

    def get(self, request, pk, *args, **kwargs):
        """
        Get info for a specific licence
        """
        try:
            licence = Licence.objects.get(id=pk)
        except Licence.DoesNotExist:
            return Response({"status": "No matching licence"}, status.HTTP_400_BAD_REQUEST)

        hmrc_mail_status = licence.hmrc_mail_status()
        return Response({"hmrc_mail_status": hmrc_mail_status}, status.HTTP_200_OK)


class HMRCIntegration(UpdateAPIView):
    authentication_classes = (HMRCIntegrationOnlyAuthentication,)

    def put(self, request, *args, **kwargs):
        """Update Good Usages for a batch of Licences"""

        serializer = HMRCIntegrationUsageDataLicencesSerializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse(data={**request.data, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        usage_data_id = serializer.validated_data["usage_data_id"]
        if HMRCIntegrationUsageData.objects.filter(id=usage_data_id).exists():
            return JsonResponse(data={"usage_data_id": usage_data_id}, status=HTTP_208_ALREADY_REPORTED)

        valid_licences, invalid_licences = validate_licence_usage_updates(serializer.validated_data["licences"])

        if valid_licences:
            save_licence_usage_updates(usage_data_id, valid_licences)

        return JsonResponse(
            data={
                "usage_data_id": usage_data_id,
                "licences": {"accepted": valid_licences, "rejected": invalid_licences},
            },
            status=status.HTTP_207_MULTI_STATUS,
        )
