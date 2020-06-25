from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import UpdateAPIView
from rest_framework.status import HTTP_208_ALREADY_REPORTED

from conf.authentication import HMRCIntegrationOnlyAuthentication
from licences.libraries.hmrc_integration_operations import validate_licence_usage_updates, save_licence_usage_updates
from licences.models import HMRCIntegrationUsageUpdate
from licences.serializers.hmrc_integration import HMRCIntegrationUsageUpdateLicencesSerializer


class HMRCIntegration(UpdateAPIView):
    authentication_classes = (HMRCIntegrationOnlyAuthentication,)

    def put(self, request, *args, **kwargs):
        """Update Good Usages for a batch of Licences"""

        serializer = HMRCIntegrationUsageUpdateLicencesSerializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse(data={**request.data, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        transaction_id = serializer.validated_data["transaction_id"]
        if HMRCIntegrationUsageUpdate.objects.filter(id=transaction_id).exists():
            return JsonResponse(data={"transaction_id": transaction_id}, status=HTTP_208_ALREADY_REPORTED)

        valid_licences, invalid_licences = validate_licence_usage_updates(serializer.validated_data["licences"])

        if valid_licences:
            save_licence_usage_updates(transaction_id, valid_licences)

        return JsonResponse(
            data={
                "transaction_id": transaction_id,
                "licences": {"accepted": valid_licences, "rejected": invalid_licences},
            },
            status=status.HTTP_207_MULTI_STATUS,
        )
