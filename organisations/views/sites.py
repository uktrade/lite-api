from django.db import transaction, connection
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from conf.constants import ExporterPermissions
from conf.permissions import assert_user_has_permission
from organisations import service
from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.libraries.get_site import get_site
from organisations.models import Organisation, Site
from organisations.serializers import SiteViewSerializer, SiteSerializer, SiteListSerializer
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
        if isinstance(request.user, ExporterUser):
            sites = Site.objects.get_by_user_and_organisation(request.user, org_pk).exclude(
                address__country__id__in=request.GET.getlist("exclude")
            )
        else:
            sites = Site.objects.filter(organisation=org_pk)

        sites = list(sites.select_related("address", "foreign_address"))
        sites.sort(key=lambda x: x.id == x.organisation.primary_site.id, reverse=True)
        serializer_data = SiteListSerializer(sites, many=True).data
        service.populate_users_count(org_pk, serializer_data)

        return JsonResponse(data={"sites": serializer_data})

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
            return JsonResponse(data={"site": SiteViewSerializer(site).data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SiteDetail(APIView):
    """
    Show details for for a specific site/edit site
    """

    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk, site_pk):
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_SITES, org_pk)
        site = get_site(site_pk, org_pk)

        serializer = SiteViewSerializer(site)
        return JsonResponse(data={"site": serializer.data})

    @transaction.atomic
    def put(self, request, org_pk, site_pk):
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_SITES, org_pk)
        site = get_site(site_pk, org_pk)

        serializer = SiteSerializer(instance=site, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            return JsonResponse(data={"site": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=400)
