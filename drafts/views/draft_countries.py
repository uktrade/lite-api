from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from drafts.libraries.get_draft import get_draft, get_draft_with_organisation
from drafts.models import CountryOnDraft
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

        countries_ids = CountryOnDraft.objects.filter(draft=draft).values_list('country', flat=True)
        countries = Country.objects.filter(id__in=countries_ids)
        serializer = CountrySerializer(countries, many=True)
        return JsonResponse(data={'countries': serializer.data})

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
        CountryOnDraft.objects.filter(draft=draft).delete()

        # Append new SitesOnDrafts
        for country in countries:
            CountryOnDraft(country=get_country(country), draft=draft).save()

        response = self.get(request, pk)
        response.status_code = status.HTTP_201_CREATED
        return response
