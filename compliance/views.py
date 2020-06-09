from django.http import JsonResponse
from rest_framework.generics import ListCreateAPIView, ListAPIView

from compliance.models import OpenLicenceReturns
from compliance.serializers import OpenLicenceReturnsCreateSerializer
from conf.authentication import ExporterAuthentication


class OpenLicenceReturnsView(ListAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = OpenLicenceReturnsCreateSerializer

    def get_queryset(self):
        return OpenLicenceReturns.objects.all()

    def post(self, request):
        x = 1
        return JsonResponse(data={"licences": ["1"]})

