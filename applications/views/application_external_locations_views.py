from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.libraries.get_applications import get_application
from applications.models import SiteOnApplication, ExternalLocationOnApplication
from applications.serializers import ExternalLocationOnApplicationSerializer
from conf.authentication import ExporterAuthentication
from organisations.libraries.get_external_location import get_external_location_with_organisation
from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.models import ExternalLocation
from organisations.serializers import ExternalLocationSerializer


class ApplicationExternalLocations(APIView):
    """
    View sites belonging to a draft or add them
    """
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        draft = get_application(pk, submitted=False)

        external_locations_ids = ExternalLocationOnApplication.objects.filter(application=draft).values_list(
            'external_location', flat=True)
        external_locations = ExternalLocation.objects.filter(id__in=external_locations_ids)
        serializer = ExternalLocationSerializer(external_locations, many=True)
        return JsonResponse(data={'external_locations': serializer.data})

    @transaction.atomic
    def post(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        external_locations = data.get('external_locations')
        draft = get_application(pk, submitted=False)

        # Validate that there are actually external locations
        if external_locations is None or len(external_locations) == 0:
            return JsonResponse(data={'errors': {
                'external_locations': [
                    'You have to pick at least one location'
                ]
            }}, status=400)

        # Validate each external location belongs to the organisation
        for external_location in external_locations:
            get_external_location_with_organisation(external_location, organisation)

        # Update draft activity
        draft.activity = 'Brokering'
        draft.save()

        # Delete existing ExternalLocationsOnDrafts
        if data.get('method') != 'append_location':
            ExternalLocationOnApplication.objects.filter(application=draft).delete()

        # Append new ExternalLocationOnDrafts
        response_data = []
        for external_location in external_locations:
            serializer = ExternalLocationOnApplicationSerializer(
                data={'external_location': external_location, 'application': str(pk)})
            if serializer.is_valid():
                serializer.save()
                response_data.append(serializer.data)
            else:
                return JsonResponse(data={'errors': serializer.errors},
                                    status=400)

        # Deletes any sites on the draft if an external location is being added
        SiteOnApplication.objects.filter(application=draft).delete()

        return JsonResponse(data={'external_locations': response_data},
                            status=status.HTTP_201_CREATED)
