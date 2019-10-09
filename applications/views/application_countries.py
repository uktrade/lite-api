from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from applications.libraries.get_applications import get_application
from applications.models import CountryOnApplication
from conf.authentication import ExporterAuthentication
from conf.decorators import only_draft_types
from organisations.libraries.get_organisation import get_organisation_by_user
from static.countries.helpers import get_country
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class ApplicationCountries(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        View countries belonging to an open licence draft
        """
        draft = get_application(pk, submitted=False)
        countries_data = []

        if draft.licence_type == ApplicationLicenceType.OPEN_LICENCE:
            countries = Country.objects.filter(countries_on_application__application=draft)
            countries_data = CountrySerializer(countries, many=True).data

        return JsonResponse(data={'countries': countries_data})

    @only_draft_types(ApplicationLicenceType.OPEN_LICENCE, filter_by_users_organisation=True)
    @transaction.atomic
    def post(self, request, draft):
        """
        Add countries to an open licence draft
        """
        data = request.data
        countries = data.get('countries')

        # Validate that there are actually countries
        if not countries:
            return JsonResponse(data={'errors': {
                'countries': [
                    'You have to pick at least one country'
                ]
            }}, status=400)

        # Delete existing SitesOnDrafts
        CountryOnApplication.objects.filter(application=draft).delete()

        # Append new SitesOnDrafts
        for country in countries:
            CountryOnApplication(country=get_country(country), application=draft).save()

        response = self.get(request, draft.id)
        response.status_code = status.HTTP_201_CREATED
        return response
