from rest_framework.exceptions import PermissionDenied

from conf.constants import Permission


def assert_user_has_permission(user, permission: Permission):
    user_permissions = user.role.permissions.values_list("id", flat=True)
    if permission.name in user_permissions:
        return True
    else:
        raise PermissionDenied()
