from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from api.conf.authentication import ExporterAuthentication
from open_general_licences.helpers import get_open_general_licence
from organisations.libraries.get_organisation import get_request_user_organisation


class Create(APIView):
    authentication_classes = (ExporterAuthentication,)

    def post(self, request, *args, **kwargs):
        organisation = get_request_user_organisation(request)
        open_general_licence = get_open_general_licence(request.data.get("open_general_licence"))
        open_general_licence_id, registrations = organisation.register_open_general_licence(
            open_general_licence, request.user
        )
        return JsonResponse(
            data={"open_general_licence": open_general_licence_id, "registrations": registrations},
            status=status.HTTP_201_CREATED,
        )
