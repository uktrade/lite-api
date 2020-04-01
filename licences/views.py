from rest_framework.generics import ListCreateAPIView

from conf.authentication import ExporterAuthentication
from licences.models import Licence
from licences.serializers import LicenceListSerializer


class Licences(ListCreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = LicenceListSerializer
    queryset = Licence.objects.all()
