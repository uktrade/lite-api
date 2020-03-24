from typing import Union, List

from django.db.models import QuerySet
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError

from applications.constants import TRANSHIPMENT_BANNED_COUNTRIES
from applications.libraries.case_status_helpers import get_case_statuses
from applications.models import BaseApplication, SiteOnApplication, ExternalLocationOnApplication
from audit_trail import service as audit_trail_service
from audit_trail.payload import AuditType
from cases.enums import CaseTypeReferenceEnum
from lite_content.lite_api.strings import ExternalLocations
from organisations.models import Site
from users.models import ExporterUser

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
        raise ValidationError({"sites": ["Your goods have already departed"]})

    # Sites can't be set if the case is in a read only state
    if application.status.status in get_case_statuses(read_only=True):
        raise ValidationError({"sites": [f"Application status {application.status.status} is read-only"]})

    # Transhipment applications can't have sites based in certain countries
    if application.case_type.reference == CaseTypeReferenceEnum.SITL:
        is_site_in_banned_location = (
            new_sites.annotate(country=Coalesce("address__country_id", "foreign_address__country_id"))
            .values_list("country")
            .filter(country__in=TRANSHIPMENT_BANNED_COUNTRIES)
            .count()
        )
        if is_site_in_banned_location:
            raise ValidationError({"sites": [ExternalLocations.Errors.TRANSHIPMENT_GB]})

    # It's possible for users to modify sites as long as sites they add are in countries
    # already on the application
    if not application.is_major_editable():
        old_countries = sites_on_application.annotate(
            country=Coalesce("site__address__country_id", "site__foreign_address__country_id")
        ).values_list("country")
        new_countries = new_sites.annotate(
            country=Coalesce("address__country_id", "foreign_address__country_id")
        ).values_list("country")
        difference = new_countries.exclude(country__in=old_countries)

        if difference:
            raise ValidationError({"sites": ["Sites have to be in the same country on minor edits"]})

    removed_sites = sites_on_application.exclude(site__id__in=new_sites)
    added_sites = new_sites.exclude(id__in=sites_on_application.values_list("site__id", flat=True))
    removed_locations = ExternalLocationOnApplication.objects.filter(application=application)

    _set_activity(
        user=user,
        application=application,
        removed_locations=removed_locations,
        removed_sites=removed_sites,
        added_sites=added_sites,
    )

    # Save the new sites
    for site in added_sites:
        SiteOnApplication.objects.create(site=site, application=application)

    removed_sites.delete()
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
