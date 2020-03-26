from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.constants import TRANSHIPMENT_BANNED_COUNTRIES
from applications.libraries.case_status_helpers import get_case_statuses
from applications.models import SiteOnApplication, ExternalLocationOnApplication
from applications.serializers.location import ExternalLocationOnApplicationSerializer
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.enums import CaseTypeReferenceEnum
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users, application_in_non_readonly_state
from lite_content.lite_api.strings import ExternalLocations
from organisations.libraries.get_external_location import get_location
from organisations.libraries.get_site import has_previous_sites
from organisations.models import ExternalLocation
from organisations.serializers import ExternalLocationSerializer
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.case_status_validate import is_case_status_draft
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
    @application_in_non_readonly_state()
    def post(self, request, application):
        data = request.data
        location_ids = data.get("external_locations")

        errors = self._validate_request(application, location_ids)
        if errors:
            return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        previous_locations = ExternalLocationOnApplication.objects.filter(application=application)
        previous_location_ids = [
            str(previous_location_id)
            for previous_location_id in previous_locations.values_list("external_location__id", flat=True)
        ]

        new_locations, errors = self._get_new_locations(
            application, request.user.organisation, location_ids, previous_locations, previous_location_ids
        )
        if errors:
            return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # Update activity
        application.activity = self.BROKERING
        application.save()

        external_locations, errors = self._set_locations_and_sites(
            data.get("method"),
            previous_location_ids,
            location_ids,
            previous_locations,
            new_locations,
            application,
            request.user,
        )
        if errors:
            return JsonResponse(data={"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data={"external_locations": external_locations}, status=status.HTTP_201_CREATED)

    def _set_locations_and_sites(
        self, method, previous_location_ids, location_ids, previous_locations, new_locations, application, user
    ):
        # Get locations to be removed
        removed_locations = []
        if method != "append_location":
            removed_location_ids = list(set(previous_location_ids) - set(location_ids))
            removed_locations = previous_locations.filter(external_location__id__in=removed_location_ids)

        # Append new ExternalLocationOnApplications
        external_locations = []
        for new_location in new_locations:
            serializer = ExternalLocationOnApplicationSerializer(
                data={"external_location": str(new_location.id), "application": str(application.id)}
            )

            if application.case_type.reference == CaseTypeReferenceEnum.SITL:
                if new_location.country.id in TRANSHIPMENT_BANNED_COUNTRIES:
                    return None, {"external_locations": [ExternalLocations.Errors.TRANSHIPMENT_GB]}

            if serializer.is_valid():
                serializer.save()
                external_locations.append(serializer.data)
            else:
                return None, serializer.errors

        # Get sites to be removed if a site is being added
        removed_sites = SiteOnApplication.objects.filter(application=application)

        if removed_sites:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.REMOVED_SITES_FROM_APPLICATION,
                target=application.get_case(),
                payload={"sites": [site.site.name for site in removed_sites]},
            )

        if removed_locations:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.REMOVED_EXTERNAL_LOCATIONS_FROM_APPLICATION,
                target=application.get_case(),
                payload={
                    "locations": [
                        location.external_location.name + " " + location.external_location.country.name
                        for location in removed_locations
                    ]
                },
            )

        if new_locations:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.ADD_EXTERNAL_LOCATIONS_TO_APPLICATION,
                target=application.get_case(),
                payload={"locations": [location.name + " " + location.country.name for location in new_locations]},
            )

        if method != "append_location":
            removed_locations.delete()

        removed_sites.delete()
        return external_locations, None

    def _validate_request(self, application, location_ids):
        # Validate that have_goods_departed isn't True
        if getattr(application, "have_goods_departed", False):
            return {"external_locations": ["Application has have_goods_departed set to True"]}
        # Validate that there are actually external locations
        if not location_ids:
            return {"external_locations": ["You have to pick at least one external location"]}

    def _get_new_locations(
        self, application, user_organisation, location_ids, previous_locations, previous_location_ids
    ):
        new_locations = []

        if (
            is_case_status_draft(application.status.status)
            or application.status.status == CaseStatusEnum.APPLICANT_EDITING
        ):
            new_locations = [
                get_location(location_id, user_organisation)
                for location_id in location_ids
                if location_id not in previous_location_ids
            ]
        else:
            if has_previous_sites(application):
                return (
                    None,
                    {
                        "external_locations": [
                            "Go back and change your answer from ‘Change a site, or delete a good, third party or "
                            "country’ to ’Change something else’."
                        ]
                    },
                )

            previous_location_countries = list(
                previous_locations.values_list("external_location__country__id", flat=True)
            )

            for location_id in location_ids:
                new_location = get_location(location_id, user_organisation)

                if previous_location_countries and new_location.country.id not in previous_location_countries:
                    return (
                        None,
                        {
                            "external_locations": [
                                "Go back and change your answer from ‘Change a site, or delete a good, "
                                "third party or country’ to ’Change something else’."
                            ]
                        },
                    )
                elif str(new_location.id) not in previous_location_ids:
                    new_locations.append(new_location)

        return new_locations, None


class ApplicationRemoveExternalLocation(APIView):
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def delete(self, request, application, ext_loc_pk):
        if not is_case_status_draft(application.status.status) and application.status.status in get_case_statuses(
            read_only=True
        ):
            return JsonResponse(
                data={"error": f"Application status {application.status.status} is read-only."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not is_case_status_draft(application.status.status)
            and application.status.status != CaseStatusEnum.APPLICANT_EDITING
        ):
            if ExternalLocationOnApplication.objects.filter(application=application).count() == 1:
                return JsonResponse(
                    data={
                        "errors": {
                            "external_locations": [
                                "Go back and change your answer from ‘Change a site, or delete a good, "
                                "third party or country’ to ’Change something else’."
                            ]
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        removed_locations = ExternalLocationOnApplication.objects.filter(
            application=application, external_location__pk=ext_loc_pk
        )

        if removed_locations:
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.REMOVED_EXTERNAL_LOCATIONS_FROM_APPLICATION,
                target=application.get_case(),
                payload={
                    "locations": [
                        location.external_location.name + " " + location.external_location.country.name
                        for location in removed_locations
                    ]
                },
            )

        removed_locations.delete()

        return JsonResponse(data={"success": "External location deleted"}, status=status.HTTP_204_NO_CONTENT)
