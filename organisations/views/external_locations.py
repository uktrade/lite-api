import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from organisations.models import ExternalLocation
from organisations.serializers import ExternalLocationSerializer


class ExternalLocationList(APIView):
    authentication_classes = (ExporterAuthentication,)
    """
    List all sites for an organisation/create site
    """

    def get(self, request, org_pk):
        external_locations = ExternalLocation.objects.filter(organisation=org_pk)
        serializer = ExternalLocationSerializer(external_locations, many=True)
        return JsonResponse(data={"external_locations": serializer.data})

    @transaction.atomic
    def post(self, request, org_pk):
        with reversion.create_revision():
            data = JSONParser().parse(request)
            data["organisation"] = org_pk
            serializer = ExternalLocationSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(
                    data={"external_location": serializer.data},
                    status=status.HTTP_201_CREATED,
                )

            return JsonResponse(
                data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )
