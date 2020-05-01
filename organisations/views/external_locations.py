from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from cases.enums import CaseTypeReferenceEnum
from conf.authentication import ExporterAuthentication
from organisations.models import ExternalLocation
from organisations.serializers import ExternalLocationSerializer, SiclExternalLocationSerializer


class ExternalLocationList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, org_pk):
        external_locations = ExternalLocation.objects.filter(organisation=org_pk).exclude(
            country__id__in=request.GET.getlist("exclude")
        )
        serializer = ExternalLocationSerializer(external_locations, many=True)
        return JsonResponse(data={"external_locations": serializer.data})

    @transaction.atomic
    def post(self, request, org_pk):
        data = request.data
        data["organisation"] = org_pk

        if data.get("application_type") == CaseTypeReferenceEnum.SICL:
            serializer = SiclExternalLocationSerializer(data=data)
        else:
            serializer = ExternalLocationSerializer(data=data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse(data={"external_location": serializer.data}, status=status.HTTP_201_CREATED,)
