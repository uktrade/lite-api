from typing import Union, List

from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from api.applications.constants import TRANSHIPMENT_AND_TRADE_CONTROL_BANNED_COUNTRIES
from api.applications.libraries.case_status_helpers import get_case_statuses
from api.applications.models import BaseApplication, SiteOnApplication, ExternalLocationOnApplication
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from cases.enums import CaseTypeEnum
from lite_content.lite_api.strings import ExternalLocations, Applications
from api.organisations.models import Site
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.models import ExporterUser

TRADING = "Trading"


def add_sites_to_application(user: ExporterUser, new_sites: Union[QuerySet, List[Site]], application: BaseApplication):
    """
    Add sites to an application, handle validation and audit
    """
    sites_on_application = SiteOnApplication.objects.filter(application=application)

    if not new_sites:
        raise ValidationError({"sites": ["Select at least one site"]})

    # Users don't specify their goods locations if they've already departed
    if getattr(application, "have_goods_departed", False):
        raise ValidationError({"sites": [Applications.Generic.GOODS_ALREADY_DEPARTED]})

    # Sites can't be set if the case is in a read only state
    if application.status.status in get_case_statuses(read_only=True):
        raise ValidationError({"sites": [f"Application status {application.status.status} is read-only"]})

    # Transhipment and Trade Control applications can't have sites based in certain countries
    if application.case_type.id in [*CaseTypeEnum.trade_control_case_type_ids(), CaseTypeEnum.SITL.id]:
        banned_sites = new_sites.filter(
            address__country_id__in=TRANSHIPMENT_AND_TRADE_CONTROL_BANNED_COUNTRIES
        ).values_list("address__country_id", flat=True)

        if banned_sites:
            raise ValidationError(
                {
                    "sites": [
                        ExternalLocations.Errors.COUNTRY_ON_APPLICATION
                        % (", ".join(banned_sites), application.case_type.reference)
                    ]
                }
            )

    # It's possible for users to modify sites as long as sites they add are in countries
    # already on the application
    if not application.is_major_editable():
        old_countries = sites_on_application.values_list("site__address__country")
        difference = new_sites.exclude(address__country__in=old_countries)

        if difference:
            raise ValidationError({"sites": ["Sites have to be in the same country on minor edits"]})

    removed_sites_on_application = sites_on_application.exclude(site__id__in=new_sites)
    added_sites = new_sites.exclude(id__in=sites_on_application.values_list("site__id", flat=True))
    removed_locations = ExternalLocationOnApplication.objects.filter(application=application)

    _set_activity(
        user=user,
        application=application,
        removed_locations=removed_locations,
        removed_sites=removed_sites_on_application,
        added_sites=added_sites,
    )

    # Check if site has been removed and if it is no longer used on other applications set "is_used_on_application" to False
    # Only do this for minor/major edits
    if application.status.status != CaseStatusEnum.DRAFT:
        removed_site_ids = removed_sites_on_application.values_list("site_id", flat=True)
        if removed_site_ids:
            sites_still_on_other_applications = (
                SiteOnApplication.objects.exclude(application=application)
                .exclude(application__status__status="draft")
                .filter(site__id__in=removed_site_ids)
            )
            removed_sites_no_longer_on_other_applications = removed_sites_on_application.exclude(
                site__id__in=sites_still_on_other_applications.values_list("site_id", flat=True)
            )

            removed_sites = Site.objects.filter(
                id__in=removed_sites_no_longer_on_other_applications.values_list("site_id", flat=True)
            )
            removed_sites.update(is_used_on_application=False)

        # Set "is_used_on_application" to True for sites that have been added
        added_sites.update(is_used_on_application=True)

    # Save the new sites
    SiteOnApplication.objects.bulk_create(
        [SiteOnApplication(site=site, application=application) for site in added_sites]
    )

    removed_sites_on_application.delete()
    removed_locations.delete()

    # Update application activity
    application.activity = TRADING
    application.save()


def _set_activity(user, application, removed_locations, removed_sites, added_sites):
    case = application.get_case()
    if removed_sites:
        audit_trail_service.create(
            actor=user,
            verb=AuditType.REMOVED_SITES_FROM_APPLICATION,
            target=case,
            payload={"sites": [site.site.name for site in removed_sites],},
        )

    if removed_locations:
        audit_trail_service.create(
            actor=user,
            verb=AuditType.REMOVED_EXTERNAL_LOCATIONS_FROM_APPLICATION,
            target=case,
            payload={
                "locations": [
                    location.external_location.name + " " + location.external_location.country.name
                    for location in removed_locations
                ]
            },
        )

    if added_sites:
        audit_trail_service.create(
            actor=user,
            verb=AuditType.ADD_SITES_TO_APPLICATION,
            target=case,
            payload={"sites": [site.name for site in added_sites],},
        )
