from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser

from api.core.authentication import GovAuthentication
from api.external_data import models, serializers


class DenialViewSet(viewsets.ModelViewSet):
    queryset = models.Denial.objects.all()
    authentication_classes = (GovAuthentication,)
    parser_classes = [MultiPartParser]

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.DenialFromCSVFileSerializer
        return serializers.DenialSerializer

    def perform_create(self, serializer):
        pass
