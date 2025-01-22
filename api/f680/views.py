from rest_framework.generics import CreateAPIView

from api.core.authentication import ExporterAuthentication
from .serializers import F680Serializer
from .models import F680Application


class F680View(CreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    queryset = F680Application.objects.all()  # /PS-IGNORE
    serializer_class = F680Serializer  # /PS-IGNORE
    breakpoint()
