from django.http import JsonResponse
from rest_framework.generics import ListAPIView

from compliance.helpers import read_and_validate_csv
from compliance.models import OpenLicenceReturns
from compliance.serializers import OpenLicenceReturnsCreateSerializer
from conf.authentication import ExporterAuthentication


class OpenLicenceReturnsView(ListAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = OpenLicenceReturnsCreateSerializer

    def get_queryset(self):
        return OpenLicenceReturns.objects.all()

    def post(self, request):
        read_and_validate_csv(request.data.get("file"))
        return JsonResponse(data={"licences": ["1"]})

