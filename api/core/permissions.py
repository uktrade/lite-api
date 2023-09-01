from rest_framework import permissions

from api.core.exceptions import PermissionDeniedError
from api.organisations.models import Organisation
from api.users.models import GovUser


def assert_user_has_permission(user, permission, organisation: Organisation = None):
    if isinstance(user, GovUser):
        if user.has_permission(permission):
            return True
        else:
            raise PermissionDeniedError()
    else:
        if user.has_permission(permission, organisation):
            return True
        else:
            raise PermissionDeniedError()


def check_user_has_permission(user, permission, organisation: Organisation = None):
    if isinstance(user, GovUser):
        return user.has_permission(permission)
    else:
        return user.has_permission(permission, organisation)


class IsExporterInOrganisation(permissions.BasePermission):
    def has_permission(self, request, view):
        organisation = view.get_organisation()
        return request.user.exporteruser.is_in_organisation(organisation)
