from django.http import JsonResponse
from django.db import transaction
from api.applications.exporter.views.mixins import ExporterApplicationMixin
from api.applications.models import ApplicationDocument
from api.cases.models import Case
from rest_framework.generics import GenericAPIView, RetrieveAPIView, ListCreateAPIView

from rest_framework import status

from api.applications.exporter.permissions import CaseStatusExporterChangeable
from api.applications.exporter.serializers import (
    ApplicationChangeStatusSerializer,
    ApplicationHistorySerializer,
    ExporterApplicationDocumentSerializer,
)
from api.applications.helpers import get_application_view_serializer
from api.core.permissions import IsExporterInOrganisation
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class ApplicationChangeStatus(ExporterApplicationMixin, GenericAPIView):
    permission_classes = [
        IsExporterInOrganisation,
        CaseStatusExporterChangeable,
    ]
    serializer_class = ApplicationChangeStatusSerializer

    @transaction.atomic
    def post(self, request, pk):
        application = self.get_object()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        application.change_status(request.user, get_case_status_by_status(data["status"]), data["note"])

        response_data = get_application_view_serializer(application)(
            application, context={"user_type": request.user.type}
        ).data

        return JsonResponse(data=response_data, status=status.HTTP_200_OK)


class ApplicationHistory(ExporterApplicationMixin, RetrieveAPIView):

    lookup_field = "pk"
    queryset = Case.objects.all()
    serializer_class = ApplicationHistorySerializer


class ApplicationDocumentView(ExporterApplicationMixin, ListCreateAPIView):
    serializer_class = ExporterApplicationDocumentSerializer
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        return ApplicationDocument.objects.filter(application_id=self.application.pk)
