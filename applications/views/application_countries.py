from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from applications.models import CountryOnApplication
from conf.authentication import ExporterAuthentication
from conf.decorators import only_applications, authorised_users
from static.countries.helpers import get_country
from static.countries.models import Country
from static.countries.serializers import CountrySerializer
from users.models import ExporterUser


class ApplicationCountries(APIView):
    authentication_classes = (ExporterAuthentication,)

    @only_applications(ApplicationLicenceType.OPEN_LICENCE, can_be_edited=False)
    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        View countries belonging to an open licence application
        """
        countries = Country.objects.filter(countries_on_application__application=application)
        countries_data = CountrySerializer(countries, many=True).data

        return JsonResponse(data={'countries': countries_data}, status=status.HTTP_200_OK)

    @transaction.atomic
    @only_applications(ApplicationLicenceType.OPEN_LICENCE, can_be_edited=True)
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Add countries to an open licence application
        """
        data = request.data
        countries = data.get('countries')

        # Validate that there are actually countries
        if not countries:
            return JsonResponse(data={'errors': {
                'countries': [
                    'You have to pick at least one country'
                ]
            }}, status=status.HTTP_400_BAD_REQUEST)

        countries = [get_country(country) for country in countries]

        # Delete existing Countries from application
        CountryOnApplication.objects.filter(application=application).delete()

        # Append new Countries to application
        for country in countries:
            CountryOnApplication(country=country, application=application).save()

        countries_data = CountrySerializer(countries, many=True).data
        return JsonResponse(data={'countries': countries_data}, status=status.HTTP_201_CREATED)
