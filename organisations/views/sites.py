from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from api.conf.authentication import SharedAuthentication
from api.conf.constants import ExporterPermissions
from api.conf.helpers import str_to_bool
from api.conf.permissions import assert_user_has_permission
from lite_content.lite_api import strings
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

        if request.GET.get("postcode"):
            sites = sites.filter(address__postcode=request.GET.get("postcode"))

        sites = list(sites)
        sites.sort(key=lambda x: x.id == primary_site_id, reverse=True)
        serializer_data = SiteListSerializer(sites, many=True).data

        if str_to_bool(request.GET.get("get_total_users")):
            admin_users = UserOrganisationRelationship.objects.filter(
                organisation=organisation, role__permissions__id=ExporterPermissions.ADMINISTER_SITES.name
            ).values_list("user__id", flat=True)
            total_admin_users = len(admin_users)

            relationships = (
                UserOrganisationRelationship.objects.filter(sites__id__in=[site["id"] for site in serializer_data])
                .exclude(user__id__in=admin_users)
                .values("sites__id")
                .annotate(count=Count("sites__id"))
                .values("sites__id", "count")
            )

            relationships = {str(relationship["sites__id"]): relationship["count"] for relationship in relationships}

            for site in serializer_data:
                site["assigned_users_count"] = total_admin_users + relationships.get(site["id"], 0)

        return JsonResponse(data={"sites": serializer_data})

    @transaction.atomic
    def post(self, request, org_pk):
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_SITES, org_pk)

        data = request.data

        if "records_located_step" in data:
            if "site_records_stored_here" not in data:
                return JsonResponse(
                    data={"errors": {"site_records_stored_here": [strings.Site.NO_RECORDS_LOCATED_AT]}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not str_to_bool(data["site_records_stored_here"]) and "site_records_located_at" not in data:
                return JsonResponse(
                    data={"errors": {"site_records_located_at": [strings.Site.NO_SITE_SELECTED]}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        data["organisation"] = org_pk
        serializer = SiteCreateUpdateSerializer(data=data)

        if serializer.is_valid(raise_exception=True):
            if "validate_only" not in data or data["validate_only"] == "False":
                site = serializer.save()
                audit_trail_service.create(
                    actor=request.user, verb=AuditType.CREATED_SITE, target=site, payload={"site_name": site.name,},
                )
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

    def patch(self, request, *args, **kwargs):
        site_id = kwargs["pk"]
        if Site.objects.get(id=site_id).is_used_on_application:
            return JsonResponse(
                data={"errors": {"site_records_stored_here": [strings.Site.CANNOT_CHANGE_SITE_IF_ALREADY_IN_USE]}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if "site_records_stored_here" in request.data and "name" not in request.data:
            # If records are held at the same site, set site_records_located_at to own pk
            if str_to_bool(request.data["site_records_stored_here"]):
                request.data["site_records_located_at"] = site_id
            if (
                not str_to_bool(request.data["site_records_stored_here"])
                and "site_records_located_at" not in request.data
            ):
                return JsonResponse(
                    data={"errors": {"site_records_located_at": [strings.Site.NO_SITE_SELECTED]}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return self.partial_update(request, *args, **kwargs)

        if "name" in request.data and "site_records_stored_here" not in request.data:
            return self.partial_update(request, *args, **kwargs)
        else:
            return JsonResponse(
                data={"errors": {"site_records_stored_here": [strings.Site.NO_RECORDS_LOCATED_AT]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_update(self, serializer):
        original_instance = self.get_object()
        updated_instance = serializer.save()

        if updated_instance.site_records_located_at:
            # Add audit entry for records located at change
            if original_instance.site_records_located_at != updated_instance.site_records_located_at:
                audit_trail_service.create(
                    actor=self.request.user,
                    verb=AuditType.UPDATED_SITE,
                    target=updated_instance,
                    payload={
                        "key": original_instance.name,
                        "old": original_instance.site_records_located_at.name
                        if getattr(original_instance, "site_records_located_at", None)
                        else "N/A",
                        "new": updated_instance.site_records_located_at.name,
                    },
                )

        if updated_instance.name:
            # Add audit entry for site name change
            if original_instance.name != updated_instance.name:
                audit_trail_service.create(
                    actor=self.request.user,
                    verb=AuditType.UPDATED_SITE_NAME,
                    target=updated_instance,
                    payload={
                        "key": original_instance.name,
                        "old": original_instance.name,
                        "new": updated_instance.name,
                    },
                )
