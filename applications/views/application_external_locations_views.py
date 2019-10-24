from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.models import SiteOnApplication, ExternalLocationOnApplication
from applications.serializers import ExternalLocationOnApplicationSerializer
from cases.libraries.activity_types import CaseActivityType
from cases.models import CaseActivity, Case
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users
from organisations.libraries.get_external_location import get_external_location, \
    get_external_location_countries_on_application
from organisations.libraries.get_site import has_previous_sites
from organisations.models import ExternalLocation
from organisations.serializers import ExternalLocationSerializer
from static.statuses.enums import CaseStatusEnum
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
        if not external_locations:
            return JsonResponse(data={'errors': {'external_locations': ['You have to pick at least one '
                                                                        'external location']
                                                 }}, status=status.HTTP_400_BAD_REQUEST)

        new_external_locations = []

        if not application.status or application.status.status == CaseStatusEnum.APPLICANT_EDITING:
            new_external_locations = [get_external_location(external_location, request.user.organisation)
                                      for external_location in external_locations]
        else:
            if has_previous_sites(application):
                return JsonResponse(data={'errors': {
                    'sites': [
                        'You can not change from external locations to sites on this application without first '
                        'setting it to an editable status.']
                }}, status=status.HTTP_400_BAD_REQUEST)

            previous_external_location_countries = get_external_location_countries_on_application(application)

            for external_location in external_locations:
                new_external_location = get_external_location(external_location, request.user.organisation)

                if new_external_location.country.id not in previous_external_location_countries:
                    return JsonResponse(data={'errors': {
                        'sites': [
                            'You can not add external locations located in a different country to this application '
                            'without first setting it to an editable status.']
                    }}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    new_external_locations.append(new_external_location)

        # Update draft activity
        application.activity = 'Brokering'
        application.save()

        # Delete existing ExternalLocationOnApplications
        if data.get('method') != 'append_location':
            ExternalLocationOnApplication.objects.filter(application=application).delete()

        # Append new ExternalLocationOnApplications
        response_data = []
        for external_location in new_external_locations:
            serializer = ExternalLocationOnApplicationSerializer(
                data={'external_location': external_location.pk, 'application': application.id})
            if serializer.is_valid():
                serializer.save()
                response_data.append(serializer.data)
            else:
                return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Deletes any sites on the draft if an external location is being added
        _, deleted_site_count = SiteOnApplication.objects.filter(application=application).delete()

        self._set_case_activity(application, request.user, deleted_site_count, new_external_locations)

        return JsonResponse(data={'external_locations': response_data}, status=status.HTTP_201_CREATED)

    @staticmethod
    def _set_case_activity(application, user, deleted_site_count, new_external_locations):
        try:
            case = Case.objects.get(application=application)
        except Case.DoesNotExist:
            return

        if deleted_site_count:
            CaseActivity.create(activity_type=CaseActivityType.DELETE_ALL_SITES_FROM_APPLICATION,
                                case=case,
                                user=user)

        case_activity_locations = [external_location.name + ' ' +
                                   external_location.address + ' ' +
                                   external_location.country.name
                                   for external_location in new_external_locations]

        CaseActivity.create(activity_type=CaseActivityType.ADD_EXTERNAL_LOCATIONS_TO_APPLICATION,
                            case=case,
                            user=user,
                            locations=case_activity_locations)
