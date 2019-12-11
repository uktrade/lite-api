from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.libraries.case_status_helpers import get_case_statuses
from applications.models import SiteOnApplication, ExternalLocationOnApplication
from applications.serializers.location import SiteOnApplicationCreateSerializer
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.libraries.get_case import get_case
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users
from organisations.libraries.get_external_location import has_previous_locations
from organisations.libraries.get_site import get_site
from organisations.models import Site
from organisations.serializers import SiteViewSerializer
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.case_status_validate import is_case_status_draft
from users.models import ExporterUser


class ApplicationSites(APIView):
    """ View sites belonging to an application or add them. """

    authentication_classes = (ExporterAuthentication,)

    TRADING = "Trading"

    @authorised_users(ExporterUser)
    def get(self, request, application):
        sites_ids = SiteOnApplication.objects.filter(application=application).values_list("site", flat=True)
        sites = Site.objects.filter(id__in=sites_ids)
        serializer = SiteViewSerializer(sites, many=True)
        return JsonResponse(data={"sites": serializer.data})

    @transaction.atomic
    @authorised_users(ExporterUser)
    def post(self, request, application):
        data = request.data
        site_ids = data.get("sites")

        # Validate that there are sites
        if not site_ids:
            return JsonResponse(
                data={"errors": {"sites": ["You have to pick at least one site"]}}, status=status.HTTP_400_BAD_REQUEST,
            )

        previous_sites = SiteOnApplication.objects.filter(application=application)
        previous_sites_ids = [
            str(previous_site_id) for previous_site_id in previous_sites.values_list("site__id", flat=True)
        ]

        if not is_case_status_draft(application.status.status) and application.status.status in get_case_statuses(
            read_only=True
        ):
            return JsonResponse(
                data={
                    "errors": {"external_locations": [f"Application status {application.status.status} is read-only."]}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            is_case_status_draft(application.status.status)
            or application.status.status == CaseStatusEnum.APPLICANT_EDITING
        ):
            new_sites = [
                get_site(site_id, request.user.organisation)
                for site_id in site_ids
                if site_id not in previous_sites_ids
            ]
        else:
            if has_previous_locations(application):
                return JsonResponse(
                    data={
                        "errors": {
                            "sites": [
                                "Go back and change your answer from ‘Change a site, or delete a good, third party or "
                                "country’ to ’Change something else’."
                            ]
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            previous_site_countries = list(previous_sites.values_list("site__address__country_id", flat=True))
            new_sites = []

            for site_id in site_ids:
                new_site = get_site(site_id, request.user.organisation)

                if new_site.address.country.id not in previous_site_countries:
                    return JsonResponse(
                        data={
                            "errors": {
                                "sites": [
                                    "Go back and change your answer from ‘Change a site, or delete a good, third party or "
                                    "country’ to ’Change something else’."
                                ]
                            }
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif str(new_site.id) not in previous_sites_ids:
                    new_sites.append(new_site)

        # Update application activity
        application.activity = self.TRADING
        application.save()

        # Get sites to be removed
        removed_site_ids = list(set(previous_sites_ids) - set(site_ids))
        removed_sites = previous_sites.filter(site__id__in=removed_site_ids)

        # Append new SitesOnDrafts
        response_data = []
        for new_site in new_sites:
            serializer = SiteOnApplicationCreateSerializer(data={"site": new_site.id, "application": application.id})

            if not serializer.is_valid():
                return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST,)

            serializer.save()
            response_data.append(serializer.data)

        # Get external locations to be removed if a site is being added
        removed_locations = ExternalLocationOnApplication.objects.filter(application=application)

        _set_activity(
            user=request.user,
            application=application,
            removed_locations=removed_locations,
            removed_sites=removed_sites,
            added_sites=new_sites
        )

        removed_sites.delete()
        removed_locations.delete()

        return JsonResponse(data={"sites": response_data}, status=status.HTTP_201_CREATED)


def _set_activity(user, application, removed_locations, removed_sites, added_sites):
    case = application.get_case()
    if removed_sites:
        audit_trail_service.create(
            actor=user,
            verb=AuditType.REMOVED_SITES_FROM_APPLICATION,
            target=case,
            payload={
                'sites': [site.site.name + " " + site.site.address.country.name for site in removed_sites],
            }
        )

    if removed_locations:
        audit_trail_service.create(
            actor=user,
            verb=AuditType.REMOVED_EXTERNAL_LOCATIONS_FROM_APPLICATION,
            target=case,
            payload={
                'locations':  [
                    location.external_location.name + " " + location.external_location.country.name
                    for location in removed_locations
                ]
            }
        )

    if added_sites:
        audit_trail_service.create(
            actor=user,
            verb=AuditType.ADD_SITES_TO_APPLICATION,
            target=case,
            payload={
                'sites': [site.name + " " + site.address.country.name for site in added_sites],
            }
        )
