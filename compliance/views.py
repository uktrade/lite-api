from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import ListAPIView

from compliance.helpers import read_and_validate_csv, fetch_and_validate_licences
from compliance.models import OpenLicenceReturns
from compliance.serializers import OpenLicenceReturnsCreateSerializer, OpenLicenceReturnsListSerializer
from conf.authentication import ExporterAuthentication
from organisations.libraries.get_organisation import get_request_user_organisation_id


class OpenLicenceReturnsView(ListAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = OpenLicenceReturnsListSerializer

    def get_queryset(self):
        return OpenLicenceReturns.objects.all()

    def post(self, request):
        references, cleaned_text = read_and_validate_csv(request.data.get("file"))
        licence_ids = fetch_and_validate_licences(references)

        data = request.data
        data["file"] = cleaned_text
        data["licences"] = licence_ids
        data["organisation"] = get_request_user_organisation_id(request)
        serializer = OpenLicenceReturnsCreateSerializer(data=data)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return JsonResponse(data={"licences": licence_ids})
