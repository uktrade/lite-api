from rest_framework.generics import CreateAPIView

from api.organisations.libraries.get_organisation import get_request_user_organisation

from api.f680.models import F680Application  # /PS-IGNORE
from api.f680.exporter.serializers import F680Serializer  # /PS-IGNORE


class F680ApplicationView(CreateAPIView):  # /PS-IGNORE
    queryset = F680Application.objects.all()  # /PS-IGNORE
    serializer_class = F680Serializer  # /PS-IGNORE

    def get_serializer_context(self):
        serializer_context = super().get_serializer_context()

        serializer_context["organisation"] = get_request_user_organisation(self.request)

        return serializer_context
