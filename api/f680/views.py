from rest_framework.generics import CreateAPIView

from api.core.authentication import ExporterAuthentication
from api.organisations.libraries.get_organisation import get_request_user_organisation

from .serializers import F680Serializer
from .models import F680Application


class F680CreateView(CreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    queryset = F680Application.objects.all()  # /PS-IGNORE
    serializer_class = F680Serializer  # /PS-IGNORE

    def get_serializer_context(self):
        serializer_context = super().get_serializer_context()
        serializer_context["organisation"] = get_request_user_organisation(self.request)
        return serializer_context
