from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from licences.models import Licence
from licences.serializers.view_licence import LicenceWithGoodsViewSerializer


class LicencesView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        try:
            licence = Licence.objects.get_active_licence(pk)
        except Licence.DoesNotExist:
            raise NotFound({"non_field_errors": ["No licence found"]})

        data = LicenceWithGoodsViewSerializer(instance=licence).data
        return JsonResponse(data={"licence": data}, status=status.HTTP_200_OK)
