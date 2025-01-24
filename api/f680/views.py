from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView

from api.core.authentication import ExporterAuthentication
from api.core.decorators import authorised_to_view_application
from api.organisations.libraries.get_organisation import get_request_user_organisation, get_request_user_organisation_id
from api.users.models import ExporterUser

from .serializers import F680Serializer, F680ApplicationViewSerializer, F680ApplicationUpdateSerializer
from .models import F680Application
from api.applications.libraries.get_applications import get_f680_application


class F680CreateView(CreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    queryset = F680Application.objects.all()  # /PS-IGNORE
    serializer_class = F680Serializer  # /PS-IGNORE

    def get_serializer_context(self):
        serializer_context = super().get_serializer_context()
        serializer_context["organisation"] = get_request_user_organisation(self.request)
        return serializer_context


class F680Detail(RetrieveUpdateDestroyAPIView):
    authentication_classes = (ExporterAuthentication,)
    queryset = F680Application.objects.all()  # /PS-IGNORE
    serializer_class = F680ApplicationViewSerializer  # /PS-IGNORE

    @authorised_to_view_application(ExporterUser)
    def get(self, request, pk):
        """
        Retrieve an f680 application instance
        """

        application = get_f680_application(pk)
        serializer = F680ApplicationViewSerializer
        data = serializer(
            application,
            context={
                "user_type": request.user.type,
                "exporter_user": request.user.exporteruser,
                "organisation_id": get_request_user_organisation_id(request),
            },
        ).data
        return JsonResponse(data=data, status=status.HTTP_200_OK)

    @authorised_to_view_application(ExporterUser)
    def put(self, request, pk):
        application = get_f680_application(pk)
        update_serializer = F680ApplicationUpdateSerializer
        data = request.data
        serializer = update_serializer(
            application, data=data, context=get_request_user_organisation(request), partial=True
        )
        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        data.update({"pk": application.id})
        return JsonResponse(data=data, status=status.HTTP_200_OK)
