import reversion
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from organisations.libraries.get_organisation import get_organisation_by_user, get_organisation_by_pk
from organisations.libraries.get_site import get_site_with_organisation
from organisations.models import Organisation, Site, ExternalSite

from organisations.libraries.get_organisation import get_organisation_by_user
from organisations.libraries.get_site import get_site_with_organisation
from organisations.serializers import SiteViewSerializer, SiteCreateSerializer, SiteUpdateSerializer, \
    ExternalSiteSerializer


class ExternalSiteList(APIView):
    authentication_classes = (PkAuthentication,)
    """
    List all sites for an organisation/create site
    """

    def get(self, request):
        organisation = get_organisation_by_user(request.user)
        external_sites = ExternalSite.objects.filter(organisation=organisation)

        serializer = ExternalSiteSerializer(external_sites, many=True)
        return JsonResponse(data={'external_sites': serializer.data})

    @transaction.atomic
    def post(self, request):
        with reversion.create_revision():
            organisation = get_organisation_by_user(request.user)
            data = JSONParser().parse(request)
            data['organisation'] = organisation.id
            serializer = ExternalSiteSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(data={'external_site': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
