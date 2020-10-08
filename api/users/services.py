from django.db.models import QuerySet, Q

from api.core.constants import Roles
from api.users.models import BaseUser, Role, ExporterUser


def role_should_be_added(role, permissions):
    role_perms = role.permissions.values_list("id", flat=True)
    for perm in role_perms:
        if perm not in permissions:
            return False
    return True


def filter_roles_by_user_role(user: BaseUser, roles: QuerySet, organisation=None):
    if hasattr(user, "govuser"):
        permissions = user.govuser.role.permissions.values_list("id", flat=True)
    elif hasattr(user, "exporteruser"):
        permissions = user.exporteruser.get_role(organisation).permissions.values_list("id", flat=True)
    else:
        return []

    return [role for role in roles if role_should_be_added(role, permissions)]


def get_exporter_roles_by_organisation(request, org_pk, filter_by_user_role=True):
    system_ids = [Roles.EXPORTER_DEFAULT_ROLE_ID]
    if request.user.exporteruser.get_role(org_pk).id == Roles.EXPORTER_SUPER_USER_ROLE_ID:
        system_ids.append(Roles.EXPORTER_SUPER_USER_ROLE_ID)
    elif filter_by_user_role:
        return filter_roles_by_user_role(
            request.user, Role.objects.filter(Q(organisation=org_pk) | Q(id__in=system_ids)), org_pk,
        )
    return Role.objects.filter(Q(organisation=org_pk) | Q(id__in=system_ids)).order_by("name")
