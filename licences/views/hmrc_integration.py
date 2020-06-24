from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import UpdateAPIView

from conf.authentication import HMRCIntegrationOnlyAuthentication
from licences.libraries.hmrc_integration_operations import verify_and_save_licences
from licences.serializers.hmrc_integration import HMRCIntegrationUsageUpdateLicencesSerializer


class HMRCIntegration(UpdateAPIView):
    authentication_classes = (HMRCIntegrationOnlyAuthentication,)

    def put(self, request, *args, **kwargs):
        serializer = HMRCIntegrationUsageUpdateLicencesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verify_and_save_licences(serializer.validated_data)
        return HttpResponse(status=status.HTTP_200_OK)
