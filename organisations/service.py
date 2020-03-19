from typing import List, Dict

from addresses.models import Address
from conf.constants import ExporterPermissions
from users.models import Permission, UserOrganisationRelationship


def populate_users_count(org_pk, sites: List[Dict]):
    """
    Given a list of sites, populate (for each site) how many users are assigned to it
    """
    permission = Permission.objects.get(id=ExporterPermissions.ADMINISTER_SITES.name)
    assigned_users = (
        UserOrganisationRelationship.objects.filter(sites__in=[y["id"] for y in sites])
        .distinct()
        .prefetch_related("sites")
    )
    super_users = UserOrganisationRelationship.objects.filter(
        organisation=org_pk, role__permissions__id=permission.id
    )

    for site in sites:
        assigned_relationships = [
            relationship
            for relationship in assigned_users
            if site["id"] in [str(_id) for _id in relationship.sites.all().values_list("id", flat=True)]
        ]
        for relationship in [
            relationship
            for relationship in super_users
            if relationship.id not in [x.id for x in assigned_relationships]
        ]:
            assigned_relationships.append(relationship)
        site["users_count"] = len(assigned_relationships)
