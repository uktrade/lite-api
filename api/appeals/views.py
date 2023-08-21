from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
)

from django.shortcuts import get_object_or_404

from api.core.authentication import ExporterAuthentication

from .models import (
    Appeal,
    AppealDocument,
)
from .serializers import AppealDocumentSerializer


class AppealCreateDocumentAPIView(CreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = AppealDocumentSerializer

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.appeal = get_object_or_404(Appeal, pk=self.kwargs["pk"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["appeal"] = self.appeal
        return context


class AppealDocumentAPIView(RetrieveAPIView):
    authentication_classes = (ExporterAuthentication,)
    lookup_url_kwarg = "document_pk"
    serializer_class = AppealDocumentSerializer

    def get_queryset(self):
        return AppealDocument.objects.filter(
            appeal_id=self.kwargs["pk"],
        )
