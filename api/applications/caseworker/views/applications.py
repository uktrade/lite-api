from django.http import JsonResponse
from django.db import transaction
from rest_framework.generics import GenericAPIView
from rest_framework import status

from api.applications.caseworker.permissions import CaseStatusCaseworkerChangeable
from api.applications.caseworker.serializers import ApplicationChangeStatusSerializer, ApplicationDocumentSerializer
from api.applications.caseworker.views.mixins import CaseworkerApplicationMixin
from api.applications.helpers import get_application_view_serializer
from api.applications.models import ApplicationDocument
from api.core.permissions import CaseInCaseworkerOperableStatus
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class ApplicationChangeStatus(CaseworkerApplicationMixin, GenericAPIView):
    permission_classes = [
        CaseInCaseworkerOperableStatus,
        CaseStatusCaseworkerChangeable,
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


class ApplicationDocumentView(CaseworkerApplicationMixin, GenericAPIView):
    serializer_class = ApplicationDocumentSerializer
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        return ApplicationDocument.objects.filter(application_id=self.application.pk)
