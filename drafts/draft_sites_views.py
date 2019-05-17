import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from drafts.libraries.get_draft import get_draft
from drafts.models import SitesOnDraft
from drafts.serializers import SiteOnDraftViewSerializer, SiteOnDraftBaseSerializer
from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.libraries.get_site import get_site_with_organisation
from organisations.models import Site
from organisations.serializers import SiteViewSerializer


class DraftSites(APIView):
    """
    View sites belonging to a draft or add them
    """
    authentication_classes = (PkAuthentication,)

    def get(self, request, pk):
        draft = get_draft(pk)

        sites_ids = SitesOnDraft.objects.filter(draft=draft).values_list('site', flat=True)
        sites = Site.objects.filter(id__in=sites_ids)
        serializer = SiteViewSerializer(sites, many=True)
        return JsonResponse(data={'sites': serializer.data})

    @transaction.atomic
    def post(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        draft = get_draft(pk)

        sites = data['sites']
        data['draft'] = str(pk)

        with reversion.create_revision():
            response_data = []

            # Delete existing SitesOnDrafts
            SitesOnDraft.objects.filter(draft=draft).delete()

            # Append new SitesOnDrafts
            for site in sites:
                # Validate site belongs to the organisation
                get_site_with_organisation(site, organisation)

                # If so, add it to the data
                data['site'] = site

                serializer = SiteOnDraftBaseSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    response_data.append(serializer.data)
                else:
                    return JsonResponse(data={'errors': serializer.errors},
                                        status=400)

        return JsonResponse(data={'sites': response_data},
                            status=status.HTTP_201_CREATED)
