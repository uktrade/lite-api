from rest_framework.exceptions import PermissionDenied

from organisations.models import Organisation


def assert_user_has_permission(user, permission, organisation: Organisation = None):
    if user.has_permission(permission, organisation):
        return True
    else:
        raise PermissionDenied()
