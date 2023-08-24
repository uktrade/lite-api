from rest_framework.generics import CreateAPIView

from django.http import Http404

from api.core.authentication import ExporterAuthentication

from .models import Appeal
from .serializers import AppealDocumentSerializer


class AppealDocuments(CreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = AppealDocumentSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        try:
            self.appeal = Appeal.objects.get(pk=self.kwargs["pk"])
        except Appeal.DoesNotExist:
            raise Http404()

    def get_serializer(self, *args, **kwargs):
        kwargs["appeal"] = self.appeal
        return super().get_serializer(*args, **kwargs)
