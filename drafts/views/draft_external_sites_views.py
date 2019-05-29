import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from drafts.libraries.get_draft import get_draft
from drafts.models import SiteOnDraft, ExternalSiteOnDraft
from drafts.serializers import SiteOnDraftBaseSerializer, ExternalSiteOnDraftSerializer
from organisations.libraries.get_external_site import get_external_site_with_organisation
from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.libraries.get_site import get_site_with_organisation
from organisations.models import Site, ExternalSite
from organisations.serializers import SiteViewSerializer, ExternalSiteSerializer


class DraftExternalSites(APIView):
    """
    View sites belonging to a draft or add them
    """
    authentication_classes = (PkAuthentication,)

    def get(self, request, pk):
        draft = get_draft(pk)

        external_sites_ids = ExternalSiteOnDraft.objects.filter(draft=draft).values_list('external_site', flat=True)
        external_sites = ExternalSite.objects.filter(id__in=external_sites_ids)
        serializer = ExternalSiteSerializer(external_sites, many=True)
        return JsonResponse(data={'external_sites': serializer.data})

    @transaction.atomic
    def post(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        external_sites = data.get('external_sites')
        draft = get_draft(pk)

        # Validate that there are actually sites
        if external_sites is None:
            return JsonResponse(data={'errors': {
                'external_sites': [
                    'You have to pick at least one site.'
                ]
            }}, status=400)

        if len(external_sites) == 0:
            return JsonResponse(data={'errors': {
                'external_sites': [
                        'You have to pick at least one site.'
                    ]
                }},
                status=400)

        # Validate each site belongs to the organisation
        for external_site in external_sites:
            get_external_site_with_organisation(external_site, organisation)

        # Update draft activity
        draft.activity = 'Brokering'
        draft.save()

        # Delete existing SitesOnDrafts
        ExternalSiteOnDraft.objects.filter(draft=draft).delete()

        # Append new SitesOnDrafts
        response_data = []
        for external_site in external_sites:
            serializer = ExternalSiteOnDraftSerializer(data={'external_site': external_site, 'draft': str(pk)})
            if serializer.is_valid():
                serializer.save()
                response_data.append(serializer.data)
            else:
                return JsonResponse(data={'errors': serializer.errors},
                                    status=400)

        return JsonResponse(data={'external_sites': response_data},
                            status=status.HTTP_201_CREATED)
