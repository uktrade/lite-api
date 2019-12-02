from django.db.models import QuerySet, Q

from conf.constants import Roles
from users.models import BaseUser, GovUser, Role, ExporterUser


def filter_roles_by_user_role(user: BaseUser, roles: QuerySet, organisation=None):
    if isinstance(user, GovUser):
        permissions = user.role.permissions.values_list("id", flat=True)
    elif isinstance(user, ExporterUser):
        permissions = user.get_role(organisation).permissions.values_list("id", flat=True)
    else:
        permissions = []

    filtered_roles = []
    for role in roles:
        add_role = True
        role_perms = role.permissions.values_list("id", flat=True)
        for perm in role_perms:
            if add_role and perm not in permissions:
                add_role = False
                break
        if add_role:
            filtered_roles.append(role)

    return filtered_roles


def get_exporter_roles_by_organisation(request, org_pk, filter_by_request_user_role=True):
    system_ids = [Roles.EXPORTER_DEFAULT_ROLE_ID]
    if request.user.get_role(org_pk).id == Roles.EXPORTER_SUPER_USER_ROLE_ID:
        system_ids.append(Roles.EXPORTER_SUPER_USER_ROLE_ID)
    elif filter_by_request_user_role:
        return filter_roles_by_user_role(
            request.user, Role.objects.filter(Q(organisation=org_pk) | Q(id__in=system_ids)), org_pk,
        )
    return Role.objects.filter(Q(organisation=org_pk) | Q(id__in=system_ids))
