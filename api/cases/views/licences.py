from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from api.core.authentication import GovAuthentication
from api.licences.models import Licence
from api.licences.serializers.view_licence import LicenceWithGoodsViewSerializer
from lite_content.lite_api import strings


class LicencesView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        try:
            licence = Licence.objects.get_active_licence(pk)
        except Licence.DoesNotExist:
            raise NotFound({"non_field_errors": [strings.Licences.NOT_FOUND]})

        data = LicenceWithGoodsViewSerializer(instance=licence).data
        return JsonResponse(data={"licence": data}, status=status.HTTP_200_OK)
