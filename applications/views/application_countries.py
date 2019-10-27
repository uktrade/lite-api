from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from applications.libraries.case_activity import set_countries_case_activity
from applications.models import CountryOnApplication
from conf.authentication import ExporterAuthentication
from conf.decorators import application_licence_type, authorised_users
from static.countries.helpers import get_country
from static.countries.models import Country
from static.countries.serializers import CountrySerializer
from static.statuses.enums import CaseStatusEnum
from users.models import ExporterUser


class ApplicationCountries(APIView):
    authentication_classes = (ExporterAuthentication,)

    @application_licence_type(ApplicationLicenceType.OPEN_LICENCE)
    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        View countries belonging to an open licence application
        """
        countries = Country.objects.filter(countries_on_application__application=application)
        countries_data = CountrySerializer(countries, many=True).data

        return JsonResponse(data={'countries': countries_data}, status=status.HTTP_200_OK)

    @transaction.atomic
    @application_licence_type(ApplicationLicenceType.OPEN_LICENCE)
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Add countries to an open licence application
        """
        data = request.data
        countries = data.get('countries')

        # Validate that there are actually countries
        if not countries:
            return JsonResponse(data={'errors': {'countries': ['You have to pick at least one country']}},
                                status=status.HTTP_400_BAD_REQUEST)

        previous_countries = CountryOnApplication.objects.filter(application=application)
        new_countries = []

        if not application.status or application.status.status == CaseStatusEnum.APPLICANT_EDITING:
            new_countries = [get_country(country) for country in countries]
        else:
            for country in countries:
                new_country = get_country(country)

                if new_country.id not in list(previous_countries.values_list('country_id', flat=True)):
                    return JsonResponse(
                        data={'errors': {'countries': ['You can not add new countries to this application without '
                                                       'first setting it to an editable status']}},
                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    new_countries.append(new_country)

        # Delete previous Countries from application
        _, deleted_country_count = previous_countries.delete()

        # Append new Countries to application
        for country in new_countries:
            CountryOnApplication(country=country, application=application).save()

        countries_data = CountrySerializer(new_countries, many=True).data

        set_countries_case_activity(deleted_country_count, new_countries, request.user, application)

        return JsonResponse(data={'countries': countries_data}, status=status.HTTP_201_CREATED)
