from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.libraries.case_status_helpers import get_case_statuses
from applications.models import SiteOnApplication, ExternalLocationOnApplication
from applications.serializers.location import ExternalLocationOnApplicationSerializer
from audit_trail import service as audit_trail_service
from audit_trail.constants import Verb
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users
from organisations.libraries.get_external_location import get_location
from organisations.libraries.get_site import has_previous_sites
from organisations.models import ExternalLocation
from organisations.serializers import ExternalLocationSerializer
from static.statuses.enums import CaseStatusEnum
from users.models import ExporterUser


class ApplicationExternalLocations(APIView):
    """ View sites belonging to a draft or add them. """

    authentication_classes = (ExporterAuthentication,)

    BROKERING = "Brokering"

    @authorised_users(ExporterUser)
    def get(self, request, application):
        external_locations_ids = ExternalLocationOnApplication.objects.filter(application=application).values_list(
            "external_location", flat=True
        )
        external_locations = ExternalLocation.objects.filter(id__in=external_locations_ids)
        serializer = ExternalLocationSerializer(external_locations, many=True)

        return JsonResponse(data={"external_locations": serializer.data}, status=status.HTTP_200_OK)

    @transaction.atomic
    @authorised_users(ExporterUser)
    def post(self, request, application):
        data = request.data
        location_ids = data.get("external_locations")

        # Validate that there are actually external locations
        if not location_ids:
            return JsonResponse(
                data={"errors": {"external_locations": ["You have to pick at least one external location"]}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_locations = ExternalLocationOnApplication.objects.filter(application=application)
        previous_location_ids = [
            str(previous_location_id)
            for previous_location_id in previous_locations.values_list("external_location__id", flat=True)
        ]

        if application.status and application.status.status in get_case_statuses(read_only=True):
            return JsonResponse(
                data={
                    "errors": {"external_locations": [f"Application status {application.status.status} is read-only."]}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not application.status or application.status.status == CaseStatusEnum.APPLICANT_EDITING:
            new_locations = [
                get_location(location_id, request.user.organisation)
                for location_id in location_ids
                if location_id not in previous_location_ids
            ]
        else:
            if has_previous_sites(application):
                return JsonResponse(
                    data={
                        "errors": {
                            "external_locations": [
                                "Go back and change your answer from ‘Change a site, or delete a good, third party or "
                                "country’ to ’Change something else’."
                            ]
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            previous_location_countries = list(
                previous_locations.values_list("external_location__country__id", flat=True)
            )
            new_locations = []

            for location_id in location_ids:
                new_location = get_location(location_id, request.user.organisation)

                if previous_location_countries and new_location.country.id not in previous_location_countries:
                    return JsonResponse(
                        data={
                            "errors": {
                                "external_locations": [
                                    "Go back and change your answer from ‘Change a site, or delete a good, third party or "
                                    "country’ to ’Change something else’."
                                ]
                            }
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                elif str(new_location.id) not in previous_location_ids:
                    new_locations.append(new_location)

        # Update activity
        application.activity = self.BROKERING
        application.save()

        # Get locations to be removed
        removed_locations = []
        if data.get("method") != "append_location":
            removed_location_ids = list(set(previous_location_ids) - set(location_ids))
            removed_locations = previous_locations.filter(external_location__id__in=removed_location_ids)

        # Append new ExternalLocationOnApplications
        response_data = []
        for new_location in new_locations:
            serializer = ExternalLocationOnApplicationSerializer(
                data={"external_location": new_location.id, "application": application.id,}
            )

            if serializer.is_valid():
                serializer.save()
                response_data.append(serializer.data)
            else:
                return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST,)

        # Get sites to be removed if a site is being added
        removed_sites = SiteOnApplication.objects.filter(application=application)

        if removed_sites:
            audit_trail_service.create(
                actor=request.user,
                verb=Verb.REMOVED_SITES_FROM_APPLICATION,
                target=application.get_case() or application,
                payload={
                    'sites': [site.site.name + " " + site.site.address.country.name for site in removed_sites],
                }
            )

        if removed_locations:
            audit_trail_service.create(
                actor=request.user,
                verb=Verb.REMOVED_EXTERNAL_LOCATIONS_FROM_APPLICATION,
                target=application.get_case() or application,
                payload={
                    'locations': [
                        location.external_location.name + " " + location.external_location.country.name
                        for location in removed_locations
                    ]
                }
            )

        if new_locations:
            audit_trail_service.create(
                actor=request.user,
                verb=Verb.ADDED_EXTERNAL_LOCATIONS_FROM_APPLICATION,
                target=application.get_case() or application,
                payload={
                    'locations': [location.name + " " + location.country.name for location in new_locations],
                }
            )

        if data.get("method") != "append_location":
            removed_locations.delete()

        removed_sites.delete()

        return JsonResponse(data={"external_locations": response_data}, status=status.HTTP_201_CREATED)


class ApplicationRemoveExternalLocation(APIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def delete(self, request, application, ext_loc_pk):
        if application.status and application.status.status in get_case_statuses(read_only=True):
            return JsonResponse(
                data={"error": f"Application status {application.status.status} is read-only."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if application.status and application.status.status != CaseStatusEnum.APPLICANT_EDITING:
            if ExternalLocationOnApplication.objects.filter(application=application).count() == 1:
                return JsonResponse(
                    data={
                        "error": "Go back and change your answer from ‘Change a site, or delete "
                        "a good, third party or country’ to ’Change something else’."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        removed_locations = ExternalLocationOnApplication.objects.filter(
            application=application, external_location__pk=ext_loc_pk
        )

        if removed_locations:
            audit_trail_service.create(
                actor=request.user,
                verb=Verb.REMOVED_EXTERNAL_LOCATIONS_FROM_APPLICATION,
                target=application.get_case() or application,
                payload={
                    'locations': [
                        location.external_location.name + " " + location.external_location.country.name
                        for location in removed_locations
                    ]
                }
            )

        removed_locations.delete()

        return JsonResponse(data={"success": "External location deleted"}, status=status.HTTP_204_NO_CONTENT,)
