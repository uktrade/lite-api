from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import HMRCIntegrationOnlyAuthentication
from licences.models import Licence


class HMRCIntegration(APIView):
    authentication_classes = (HMRCIntegrationOnlyAuthentication,)

    def put(self, request, *args, **kwargs):
        licences = request.data.get("licences")
        if not licences:
            JsonResponse(data={"licences": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        for licence in licences:
            licence_id = licence.get("id")
            if not licence_id:
                return JsonResponse(
                    data={"id": ["This field is required for each licence."]}, status=status.HTTP_400_BAD_REQUEST
                )

            try:
                licence = Licence.objects.get(id=licence.get("id"))
            except licence.DoesNotExist:
                return JsonResponse(
                    data={"licences": [f"'{licence_id}' does not exist."]}, status=status.HTTP_400_BAD_REQUEST
                )

            goods = licence.get("goods")
            if not goods:
                return JsonResponse(
                    data={"goods": [f"This field is required for licence '{licence_id}'"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # for good on Licence entity:
            #   licence.good.usage = goods.usage

        return JsonResponse(data={}, status=status.HTTP_200_OK)
