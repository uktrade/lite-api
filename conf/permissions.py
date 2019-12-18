from rest_framework.exceptions import PermissionDenied

from organisations.models import Organisation
from users.models import ExporterUser


def has_permission(user, permission, organisation: Organisation = None):
    if isinstance(user, ExporterUser):
        user_permissions = user.get_role(organisation).permissions.values_list("id", flat=True)
    else:
        user_permissions = user.role.permissions.values_list("id", flat=True)

    return permission.name in user_permissions


def assert_user_has_permission(user, permission, organisation: Organisation = None):
    if has_permission(user, permission, organisation):
        return True
    else:
        raise PermissionDenied()
