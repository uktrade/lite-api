from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import HMRCIntegrationOnlyAuthentication


class HMRCIntegration(APIView):
    authentication_classes = (HMRCIntegrationOnlyAuthentication,)

    def put(self, request, *args, **kwargs):
        return JsonResponse(data={}, status=status.HTTP_200_OK)
