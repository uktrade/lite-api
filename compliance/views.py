from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView

from compliance.helpers import read_and_validate_csv, fetch_and_validate_licences
from compliance.models import OpenLicenceReturns
from compliance.serializers import (
    OpenLicenceReturnsCreateSerializer,
    OpenLicenceReturnsListSerializer,
    OpenLicenceReturnsViewSerializer,
)
from conf.authentication import ExporterAuthentication
from lite_content.lite_api.strings import Compliance
from organisations.libraries.get_organisation import get_request_user_organisation_id


class OpenLicenceReturnsView(ListAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = OpenLicenceReturnsListSerializer

    def get_queryset(self):
        return OpenLicenceReturns.objects.all()

    def post(self, request):
        file = request.data.get("file")
        if not file:
            raise ValidationError({"file": [Compliance.OpenLicenceReturns.FILE_ERROR]})

        organisation_id = get_request_user_organisation_id(request)
        references, cleaned_text = read_and_validate_csv(file)
        licence_ids = fetch_and_validate_licences(references, organisation_id)

        data = request.data
        data["file"] = cleaned_text
        data["licences"] = licence_ids
        data["organisation"] = organisation_id
        serializer = OpenLicenceReturnsCreateSerializer(data=data)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return JsonResponse(data={"licences": list(references)}, status=status.HTTP_201_CREATED)


class OpenLicenceReturnDownloadView(RetrieveAPIView):
    authentication_classes = (ExporterAuthentication,)
    queryset = OpenLicenceReturns.objects.all()
    serializer_class = OpenLicenceReturnsViewSerializer
