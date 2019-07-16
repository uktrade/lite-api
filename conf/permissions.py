from rest_framework.exceptions import PermissionDenied


def has_permission(user, permission):
    user_permissions = user.role.permissions.values_list('id', flat=True)
    if permission in user_permissions:
        return True
    else:
        raise PermissionDenied()
