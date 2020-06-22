from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import HMRCIntegrationOnlyAuthentication
from licences.serializers.hmrc_integration import HMRCIntegrationLicencesUpdateSerializer


class HMRCIntegration(APIView):
    authentication_classes = (HMRCIntegrationOnlyAuthentication,)

    def put(self, request, *args, **kwargs):
        serializer = HMRCIntegrationLicencesUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return JsonResponse(data={}, status=status.HTTP_200_OK)
