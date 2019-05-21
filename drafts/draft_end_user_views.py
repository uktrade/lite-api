import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from drafts.libraries.get_draft import get_draft
from drafts.models import SitesOnDraft, EndUserOnDraft
from drafts.serializers import SiteOnDraftBaseSerializer
from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.libraries.get_site import get_site_with_organisation
from organisations.models import Site
from organisations.serializers import SiteViewSerializer


class DraftEndUser(APIView):
    """
    View EndUsers belonging to a draft or add them
    """
    authentication_classes = (PkAuthentication,)

    def get(self, request, pk):
        draft = get_draft(pk)

        end_user_ids = EndUserOnDraft.objects.filter(draft=draft).values_list('site', flat=True)
        end_users = Site.objects.filter(id__in=end_user_ids)
        serializer = SiteViewSerializer(end_users, many=True)
        return JsonResponse(data={'sites': serializer.data})

    @transaction.atomic
    def post(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        data = JSONParser().parse(request)
        end_users = data.get('endusers')
        draft = get_draft(pk)

        # Validate that there are actually sites
        if len(data.get('sites')) == 0:
            return JsonResponse(data={'errors': {
                'sites': [
                        'You have to pick at least one site.'
                    ]
                }},
                status=400)

        # Validate each site belongs to the organisation
        for end_user in end_users:
            get_site_with_organisation(end_user, organisation)

        # Update draft activity
        draft.activity = 'Trading'
        draft.save()

        # Delete existing SitesOnDrafts
        SitesOnDraft.objects.filter(draft=draft).delete()

        # Append new SitesOnDrafts
        response_data = []
        for end_user in end_users:
            serializer = SiteOnDraftBaseSerializer(data={'end_user': end_user, 'draft': str(pk)})
            if serializer.is_valid():
                serializer.save()
                response_data.append(serializer.data)
            else:
                return JsonResponse(data={'errors': serializer.errors},
                                    status=400)

        return JsonResponse(data={'sites': response_data},
                            status=status.HTTP_201_CREATED)
