import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from drafts.libraries.get_draft import get_draft
from drafts.models import SiteOnDraft, ExternalLocationOnDraft
from drafts.serializers import SiteOnDraftBaseSerializer, ExternalLocationOnDraftSerializer
from organisations.libraries.get_external_location import get_external_location_with_organisation
from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.libraries.get_site import get_site_with_organisation
from organisations.models import Site, ExternalLocation
from organisations.serializers import SiteViewSerializer, ExternalLocationSerializer


class DraftExternalLocations(APIView):
    """
    View sites belonging to a draft or add them
    """
    authentication_classes = (PkAuthentication,)

    def get(self, request, pk):
        draft = get_draft(pk)

        external_locations_ids = ExternalLocationOnDraft.objects.filter(draft=draft).values_list('external_location', flat=True)
        external_locations = ExternalLocation.objects.filter(id__in=external_locations_ids)
        serializer = ExternalLocationSerializer(external_locations, many=True)
        return JsonResponse(data={'external_locations': serializer.data})

    @transaction.atomic
    def post(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        external_locations = data.get('external_locations')
        draft = get_draft(pk)

        # Validate that there are actually sites
        if external_locations is None:
            return JsonResponse(data={'errors': {
                'external_locations': [
                    'You have to pick at least one site.'
                ]
            }}, status=400)

        if len(external_locations) == 0:
            return JsonResponse(data={'errors': {
                'external_locations': [
                        'You have to pick at least one site.'
                    ]
                }},
                status=400)

        # Validate each site belongs to the organisation
        for external_location in external_locations:
            get_external_location_with_organisation(external_location, organisation)

        # Update draft activity
        draft.activity = 'Brokering'
        draft.save()

        # Delete existing SitesOnDrafts
        if data.get('method') != 'append_location':
            ExternalLocationOnDraft.objects.filter(draft=draft).delete()

        # Append new SitesOnDrafts
        response_data = []
        for external_location in external_locations:
            serializer = ExternalLocationOnDraftSerializer(data={'external_location': external_location, 'draft': str(pk)})
            if serializer.is_valid():
                serializer.save()
                response_data.append(serializer.data)
            else:
                return JsonResponse(data={'errors': serializer.errors},
                                    status=400)

        # Deletes any sites on the draft if an external site is being added
        SiteOnDraft.objects.filter(draft=draft).delete()

        return JsonResponse(data={'external_locations': response_data},
                            status=status.HTTP_201_CREATED)
