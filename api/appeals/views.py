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
from .serializers import (
    AppealDocumentSerializer,
    AppealDocumentCreateSerializer,
)


class AppealCreateDocumentAPIView(CreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = AppealDocumentCreateSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        try:
            self.appeal = Appeal.objects.get(pk=self.kwargs["pk"])
        except Appeal.DoesNotExist:
            raise Http404()

    def get_serializer(self, *args, **kwargs):
        kwargs["appeal"] = self.appeal
        return super().get_serializer(*args, **kwargs)


class AppealDocumentAPIView(RetrieveAPIView):
    authentication_classes = (ExporterAuthentication,)
    lookup_url_kwarg = "document_pk"
    serializer_class = AppealDocumentSerializer

    def get_queryset(self):
        return AppealDocument.objects.filter(
            appeal_id=self.kwargs["pk"],
        )
