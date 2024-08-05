from django.http import Http404, JsonResponse
from rest_framework import status
from rest_framework.generics import UpdateAPIView

from api.core.authentication import ExporterAuthentication
from api.core.permissions import IsExporterInOrganisation
from api.applications.serializers.good import GoodOnApplicationQuantityValueSerializer
from api.applications.models import BaseApplication, GoodOnApplication
from api.exporter.applications.permissions import IsApplicationEditable


class BaseExporterApplication:
    authentication_classes = (ExporterAuthentication,)
    permission_classes = (IsExporterInOrganisation,)

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        try:
            self.application = BaseApplication.objects.get(pk=self.kwargs["pk"])
        except BaseApplication.DoesNotExist:
            raise Http404()

    def get_organisation(self):
        return self.application.organisation


class ApplicationQuantityValueUpdateView(BaseExporterApplication, UpdateAPIView):
    serializer_class = GoodOnApplicationQuantityValueSerializer
    permission_classes = (
        IsExporterInOrganisation,
        IsApplicationEditable,
    )

    def patch(self, request, **kwargs):
        good_on_application_pk = kwargs["good_on_application_pk"]
        good_on_application = GoodOnApplication.objects.get(pk=good_on_application_pk)

        data = request.data.copy()
        serializer = self.serializer_class(instance=good_on_application, data=data, partial=True)
        if not serializer.is_valid():
            return JsonResponse(
                data={"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()

        return JsonResponse(status=status.HTTP_200_OK, data=serializer.data)
