from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from conf.constants import ExporterPermissions
from conf.helpers import str_to_bool
from conf.permissions import assert_user_has_permission
from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.models import Site
from organisations.serializers import SiteViewSerializer, SiteCreateUpdateSerializer, SiteListSerializer
from users.models import ExporterUser, UserOrganisationRelationship


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
        organisation = get_organisation_by_pk(org_pk)
        primary_site_id = organisation.primary_site_id

        if isinstance(request.user, ExporterUser):
            sites = Site.objects.get_by_user_and_organisation(request.user, organisation).exclude(
                address__country__id__in=request.GET.getlist("exclude")
            )
        else:
            sites = Site.objects.filter(organisation=organisation)

        sites = list(sites)
        sites.sort(key=lambda x: x.id == primary_site_id, reverse=True)
        serializer_data = SiteListSerializer(sites, many=True).data

        if str_to_bool(request.GET.get("get_total_users")):
            admin_users = UserOrganisationRelationship.objects.filter(
                organisation=organisation, role__permissions__id=ExporterPermissions.ADMINISTER_SITES.name
            ).values_list("user__id", flat=True)
            total_admin_users = len(admin_users)

            for site in serializer_data:
                site["assigned_users_count"] = (
                    UserOrganisationRelationship.objects.filter(sites__id=site["id"])
                    .exclude(user__id__in=admin_users)
                    .count()
                    + total_admin_users
                )

        return JsonResponse(data={"sites": serializer_data})

    @transaction.atomic
    def post(self, request, org_pk):
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_SITES, org_pk)

        data = request.data
        data["organisation"] = org_pk
        serializer = SiteCreateUpdateSerializer(data=data)

        if serializer.is_valid(raise_exception=True):
            if "validate_only" not in data or data["validate_only"] == "False":
                site = serializer.save()
                return JsonResponse(data={"site": SiteViewSerializer(site).data}, status=status.HTTP_201_CREATED)
            return JsonResponse(data={})


class SiteRetrieveUpdate(RetrieveUpdateAPIView):
    authentication_classes = (SharedAuthentication,)

    def get_queryset(self):
        return Site.objects.filter(organisation=get_organisation_by_pk(self.kwargs["org_pk"]))

    def get_serializer_class(self):
        if isinstance(self.request.user, ExporterUser):
            assert_user_has_permission(self.request.user, ExporterPermissions.ADMINISTER_SITES, self.kwargs["org_pk"])

        if self.request.method.lower() == "get":
            return SiteViewSerializer
        else:
            return SiteCreateUpdateSerializer
