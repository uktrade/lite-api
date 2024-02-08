from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
)

from django.shortcuts import get_object_or_404

from api.core.authentication import ExporterAuthentication
from api.core.permissions import IsExporterInOrganisation
from api.core.views import DocumentStreamAPIView

from .filters import AppealFilter
from .models import (
    Appeal,
    AppealDocument,
)
from .serializers import AppealDocumentSerializer


class BaseAppealDocumentAPIView:
    authentication_classes = (ExporterAuthentication,)
    permission_classes = [IsExporterInOrganisation]
    serializer_class = AppealDocumentSerializer

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.appeal = get_object_or_404(Appeal, pk=self.kwargs["pk"])

    def get_organisation(self):
        return self.appeal.baseapplication.organisation


class AppealCreateDocumentAPIView(BaseAppealDocumentAPIView, CreateAPIView):
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["appeal"] = self.appeal
        return context


class AppealDocumentAPIView(BaseAppealDocumentAPIView, RetrieveAPIView):
    filter_backends = (AppealFilter,)
    lookup_url_kwarg = "document_pk"
    queryset = AppealDocument.objects.all()


class AppealDocumentStreamAPIView(BaseAppealDocumentAPIView, DocumentStreamAPIView):
    filter_backends = (AppealFilter,)
    lookup_url_kwarg = "document_pk"
    queryset = AppealDocument.objects.all()

    def get_document(self, instance):
        return instance
