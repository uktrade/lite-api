from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
)

from django.http import Http404
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

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        try:
            self.appeal = Appeal.objects.get(pk=self.kwargs["pk"])
        except Appeal.DoesNotExist:
            raise Http404()

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
