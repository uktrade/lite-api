from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from applications.libraries.get_applications import get_draft
from applications.models import SiteOnApplication, ExternalLocationOnApplication
from applications.serializers import SiteOnApplicationCreateSerializer
from conf.authentication import ExporterAuthentication
from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.libraries.get_site import get_site_with_organisation
from organisations.models import Site
from organisations.serializers import SiteViewSerializer


class DraftSites(APIView):
    """
    View sites belonging to a draft or add them
    """
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        draft = get_draft(pk)

        sites_ids = SiteOnApplication.objects.filter(application=draft).values_list('site', flat=True)
        sites = Site.objects.filter(id__in=sites_ids)
        serializer = SiteViewSerializer(sites, many=True)
        return JsonResponse(data={'sites': serializer.data})

    @transaction.atomic
    def post(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        sites = data.get('sites')
        draft = get_draft(pk)

        # Validate that there are actually sites
        if sites is None:
            return JsonResponse(data={'errors': {
                'sites': [
                    'You have to pick at least one site.'
                ]
            }}, status=400)

        if len(sites) == 0:
            return JsonResponse(data={'errors': {
                'sites': [
                        'You have to pick at least one site.'
                    ]
                }},
                status=400)

        # Validate each site belongs to the organisation
        for site in sites:
            get_site_with_organisation(site, organisation)

        # Update draft activity
        draft.activity = 'Trading'
        draft.save()

        # Delete existing SitesOnDrafts
        SiteOnApplication.objects.filter(application=draft).delete()

        # Append new SitesOnDrafts
        response_data = []
        for site in sites:
            serializer = SiteOnApplicationCreateSerializer(data={'site': site, 'application': str(pk)})
            if serializer.is_valid():
                serializer.save()
                response_data.append(serializer.data)
            else:
                return JsonResponse(data={'errors': serializer.errors},
                                    status=400)

        # Deletes any external sites on the draft if a site is being added
        ExternalLocationOnApplication.objects.filter(application=draft).delete()

        return JsonResponse(data={'sites': response_data},
                            status=status.HTTP_201_CREATED)
