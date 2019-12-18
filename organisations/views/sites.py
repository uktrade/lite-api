from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from conf.constants import ExporterPermissions
from conf.permissions import assert_user_has_permission
from organisations.models import Organisation, Site
from organisations.serializers import SiteViewSerializer, SiteSerializer
from users.libraries.get_user import get_user_organisation_relationship
from users.models import ExporterUser


class SitesList(APIView):
    """
    List all sites for an organisation/create site
    """
    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk):
        """
        Endpoint for listing the sites of an organisation
        filtered on whether or not the user belongs to the site
        """
        user_organisation_relationship = get_user_organisation_relationship(request.user, org_pk)

        sites = list(Site.objects.get_by_user_organisation_relationship(user_organisation_relationship))
        sites.sort(key=lambda x: x.id == x.organisation.primary_site.id, reverse=True)

        serializer = SiteViewSerializer(sites, many=True)
        return JsonResponse(data={"sites": serializer.data})

    @transaction.atomic
    def post(self, request, org_pk):
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_SITES, org_pk)

        organisation = Organisation.objects.get(pk=org_pk)
        data = JSONParser().parse(request)
        data["organisation"] = organisation.id
        serializer = SiteSerializer(data=data)

        if serializer.is_valid():
            site = serializer.save()
            return JsonResponse(data={"site":  SiteViewSerializer(site).data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SiteDetail(APIView):
    """
    Show details for for a specific site/edit site
    """

    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk, site_pk):
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_SITES, org_pk)
        Organisation.objects.get(pk=org_pk)
        site = Site.objects.get(pk=site_pk)

        serializer = SiteViewSerializer(site)
        return JsonResponse(data={"site": serializer.data})

    @transaction.atomic
    def put(self, request, org_pk, site_pk):
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_SITES, org_pk)
        Organisation.objects.get(pk=org_pk)
        site = Site.objects.get(pk=site_pk)

        serializer = SiteSerializer(instance=site, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            return JsonResponse(data={"site": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=400)
