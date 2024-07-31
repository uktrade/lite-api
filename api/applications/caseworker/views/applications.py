from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, JsonResponse
from django.db import transaction
from rest_framework.generics import GenericAPIView
from rest_framework import status

from api.applications.caseworker.permissions import CaseStatusCaseworkerChangeable
from api.applications.caseworker.serializers import ApplicationChangeStatusSerializer
from api.applications.helpers import get_application_view_serializer
from api.applications.libraries.get_applications import get_application
from api.core.exceptions import NotFoundError
from api.core.authentication import GovAuthentication
from api.core.permissions import CaseInCaseworkerOperableStatus
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class ApplicationChangeStatus(GenericAPIView):
    authentication_classes = (GovAuthentication,)
    permission_classes = [
        CaseInCaseworkerOperableStatus,
        CaseStatusCaseworkerChangeable,
    ]
    serializer_class = ApplicationChangeStatusSerializer

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        try:
            self.application = get_application(self.kwargs["pk"])
        except (ObjectDoesNotExist, NotFoundError):
            raise Http404()

    def get_object(self):
        self.check_object_permissions(self.request, self.application)
        return self.application

    def get_case(self):
        return self.application

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
