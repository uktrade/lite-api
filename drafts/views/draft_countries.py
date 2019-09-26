from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from conf.authentication import ExporterAuthentication
from drafts.libraries.get_drafts import get_draft, get_draft_with_organisation
from applications.models import CountryOnApplication
from organisations.libraries.get_organisation import get_organisation_by_user
from static.countries.helpers import get_country
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class DraftCountries(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        View countries belonging to an open licence draft
        """
        draft = get_draft(pk)
        countries_data = list()

        if draft.licence_type == ApplicationLicenceType.OPEN_LICENCE:
            countries = Country.objects.filter(countries_on_application__application=draft)
            countries_data = CountrySerializer(countries, many=True).data

        return JsonResponse(data={'countries': countries_data})

    @transaction.atomic
    def post(self, request, pk):
        """
        Add countries to an open licence draft
        """
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        countries = data.get('countries')
        draft = get_draft_with_organisation(pk, organisation)

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

        response = self.get(request, pk)
        response.status_code = status.HTTP_201_CREATED
        return response
