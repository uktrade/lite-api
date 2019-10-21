from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.models import SiteOnApplication, ExternalLocationOnApplication
from applications.serializers import SiteOnApplicationCreateSerializer
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users
from organisations.libraries.get_site import get_site_with_organisation, has_previous_external_locations, \
    get_site_countries_on_application
from organisations.models import Site
from organisations.serializers import SiteViewSerializer
from static.statuses.enums import CaseStatusEnum
from users.models import ExporterUser


class ApplicationSites(APIView):
    """
    View sites belonging to an application or add them
    """
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application):
        sites_ids = SiteOnApplication.objects.filter(application=application).values_list('site', flat=True)
        sites = Site.objects.filter(id__in=sites_ids)
        serializer = SiteViewSerializer(sites, many=True)
        return JsonResponse(data={'sites': serializer.data})

    @transaction.atomic
    @authorised_users(ExporterUser)
    def post(self, request, application):
        data = request.data
        sites = data.get('sites')

        # Validate that there are actually sites
        if not sites:
            return JsonResponse(data={'errors': {'sites': ['You have to pick at least one site.']}},
                                status=status.HTTP_400_BAD_REQUEST)

        new_sites = []

        if not application.status or application.status.status == CaseStatusEnum.APPLICANT_EDITING:
            new_sites = [get_site_with_organisation(site, request.user.organisation) for site in sites]
        elif application.status.status != CaseStatusEnum.APPLICANT_EDITING:
            if has_previous_external_locations:
                return JsonResponse(data={'errors': {
                    'sites': [
                        'You can not change from sites to external locations on this application without first '
                        'setting it to an editable status.']
                }}, status=status.HTTP_400_BAD_REQUEST)

            previous_site_countries = get_site_countries_on_application(application)

            for site in sites:
                new_site = get_site_with_organisation(site, request.user.organisation)

                if new_site.address.country not in previous_site_countries:
                    return JsonResponse(data={'errors': {
                        'sites': [
                            'You can not add sites located in a different country to this application without first '
                            'setting it to an editable status.']
                      }}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    new_sites.append(new_site)

        # Update draft activity
        application.activity = 'Trading'
        application.save()

        # Delete existing SitesOnDrafts
        SiteOnApplication.objects.filter(application=application).delete()

        # Append new SitesOnDrafts
        response_data = []
        for site in new_sites:
            serializer = SiteOnApplicationCreateSerializer(data={'site': site.pk, 'application': application.id})
            if serializer.is_valid():
                serializer.save()
                response_data.append(serializer.data)
            else:
                return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Deletes any external sites on the draft if a site is being added
        ExternalLocationOnApplication.objects.filter(application=application).delete()

        return JsonResponse(data={'sites': response_data}, status=status.HTTP_201_CREATED)
