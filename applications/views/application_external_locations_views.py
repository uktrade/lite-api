from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.models import SiteOnApplication, ExternalLocationOnApplication
from applications.serializers import ExternalLocationOnApplicationSerializer
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users
from organisations.libraries.get_external_location import get_external_location_with_organisation
from organisations.models import ExternalLocation
from organisations.serializers import ExternalLocationSerializer
from users.models import ExporterUser


class ApplicationExternalLocations(APIView):
    """
    View sites belonging to a draft or add them
    """
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application):
        external_locations_ids = ExternalLocationOnApplication.objects.filter(application=application).values_list(
            'external_location', flat=True)
        external_locations = ExternalLocation.objects.filter(id__in=external_locations_ids)
        serializer = ExternalLocationSerializer(external_locations, many=True)

        return JsonResponse(data={'external_locations': serializer.data}, status=status.HTTP_200_OK)

    @transaction.atomic
    @authorised_users(ExporterUser)
    def post(self, request, application):
        data = request.data
        external_locations = data.get('external_locations')

        # Validate that there are actually external locations
        if external_locations is None or len(external_locations) == 0:
            return JsonResponse(data={'errors': {
                'external_locations': [
                    'You have to pick at least one location'
                ]
            }}, status=status.HTTP_400_BAD_REQUEST)

        # Validate each external location belongs to the organisation
        for external_location in external_locations:
            get_external_location_with_organisation(external_location, request.user.organisation)

        # Update draft activity
        application.activity = 'Brokering'
        application.save()

        # Delete existing ExternalLocationOnApplications
        if data.get('method') != 'append_location':
            ExternalLocationOnApplication.objects.filter(application=application).delete()

        # Append new ExternalLocationOnApplications
        response_data = []
        for external_location in external_locations:
            serializer = ExternalLocationOnApplicationSerializer(
                data={'external_location': external_location, 'application': application.id})
            if serializer.is_valid():
                serializer.save()
                response_data.append(serializer.data)
            else:
                return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Deletes any sites on the draft if an external location is being added
        SiteOnApplication.objects.filter(application=application).delete()

        return JsonResponse(data={'external_locations': response_data}, status=status.HTTP_201_CREATED)
