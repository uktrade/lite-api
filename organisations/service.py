from typing import List, Dict

from django.db.models import Count

from conf.constants import ExporterPermissions
from users.models import UserOrganisationRelationship


def populate_assigned_users_count(org_pk, sites: List[Dict]):
    """
    Given a list of sites, count and display (for each site) how many users are assigned to each one
    """
    super_users = UserOrganisationRelationship.objects.filter(
        organisation=org_pk, role__permissions__id=ExporterPermissions.ADMINISTER_SITES.name
    ).values_list("id", flat=True)

    assigned_users = (
        UserOrganisationRelationship.objects.filter(sites__in=[site["id"] for site in sites])
        .exclude(id__in=super_users)
        .values("sites")
        .annotate(site_assignees_count=Count("sites"))
    )

    for site in sites:
        assigned = 0

        for relationship in assigned_users:
            if str(relationship["sites"]) == site["id"]:
                assigned = relationship["site_assignees_count"]

        site["assigned_users_count"] = len(super_users) + assigned
