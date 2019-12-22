from rest_framework.exceptions import PermissionDenied

from organisations.models import Organisation
from users.models import GovUser


def assert_user_has_permission(user, permission, organisation: Organisation = None):
    if isinstance(user, GovUser):
        if user.has_permission(permission):
            return True
        else:
            raise PermissionDenied()
    else:
        if user.has_permission(permission, organisation):
            return True
        else:
            raise PermissionDenied()
