from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationType
from applications.libraries.case_activity import set_countries_case_activity
from applications.libraries.case_status_helpers import get_case_statuses
from applications.models import CountryOnApplication
from conf.authentication import ExporterAuthentication
from conf.decorators import allowed_application_types, authorised_users
from static.countries.helpers import get_country
from static.countries.models import Country
from static.countries.serializers import CountrySerializer
from static.statuses.enums import CaseStatusEnum
from users.models import ExporterUser


class ApplicationCountries(APIView):
    authentication_classes = (ExporterAuthentication,)

    @allowed_application_types([ApplicationType.OPEN_LICENCE])
    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        View countries belonging to an open licence application
        """
        countries = Country.objects.filter(countries_on_application__application=application)
        countries_data = CountrySerializer(countries, many=True).data

        return JsonResponse(data={'countries': countries_data}, status=status.HTTP_200_OK)

    @transaction.atomic
    @allowed_application_types([ApplicationType.OPEN_LICENCE])
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """ Add countries to an open licence application. """
        data = request.data
        country_ids = data.get('countries')

        # Validate that there are countries
        if not country_ids:
            return JsonResponse(data={'errors': {'countries': ['You have to pick at least one country']}},
                                status=status.HTTP_400_BAD_REQUEST)

        if application.status and application.status.status in get_case_statuses(read_only=True):
            return JsonResponse(data={'errors': {'external_locations':
                                                     [f'Application status {application.status.status} is read-only.']
                                                 }},
                                status=status.HTTP_400_BAD_REQUEST)

        else:
            previous_countries = CountryOnApplication.objects.filter(application=application)
            previous_country_ids = [str(previous_country_id) for previous_country_id in
                                previous_countries.values_list('country__id', flat=True)]
            new_countries = []

            if not application.status or application.status.status == CaseStatusEnum.APPLICANT_EDITING:
                new_countries = [get_country(country_id) for country_id in country_ids
                                 if country_id not in previous_country_ids]
            else:
                for country_id in country_ids:
                    if previous_country_ids and country_id not in previous_country_ids:
                        return JsonResponse(
                            data={'errors': {'countries': ["Go back and change your answer from ‘Change a site, or delete "
                                                       "a good, third party or country’ to ’Change something else’."]}},
                            status=status.HTTP_400_BAD_REQUEST)

            # Get countries to be removed
            removed_country_ids = list(set(previous_country_ids) - set(country_ids))
            removed_countries = previous_countries.filter(country__id__in=removed_country_ids)

            # Append new Countries to application (only in unsubmitted/applicant editing statuses)
            for country in new_countries:
                CountryOnApplication(country=country, application=application).save()

            countries_data = CountrySerializer(new_countries, many=True).data

            set_countries_case_activity(removed_countries, new_countries, request.user, application)

            removed_countries.delete()

            return JsonResponse(data={'countries': countries_data}, status=status.HTTP_201_CREATED)
