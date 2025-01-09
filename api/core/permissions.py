from rest_framework import permissions

from api.core.constants import GovPermissions
from api.core.exceptions import PermissionDeniedError
from api.organisations.libraries.get_organisation import get_request_user_organisation
from api.organisations.models import Organisation
from api.users.models import GovUser

from lite_routing.routing_rules_internal.enums import QueuesEnum

BULK_APPROVE_ALLOWED_QUEUES = [
    QueuesEnum.MOD_CAPPROT,
    QueuesEnum.MOD_DI_DIRECT,
    QueuesEnum.MOD_DI_INDIRECT,
    QueuesEnum.MOD_DSR,
    QueuesEnum.MOD_DSTL,
]


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


def assert_user_in_role(user, role):
    if isinstance(user, GovUser):
        if user.role.id == role:
            return True
    raise PermissionDeniedError()


def check_user_has_permission(user, permission, organisation: Organisation = None):
    if isinstance(user, GovUser):
        return user.has_permission(permission)
    else:
        return user.has_permission(permission, organisation)


class IsExporterInOrganisation(permissions.BasePermission):
    def has_permission(self, request, view):
        return get_request_user_organisation(request) == view.get_organisation()


class CaseInCaseworkerOperableStatus(permissions.BasePermission):
    def has_permission(self, request, view):
        return view.get_case().status.is_caseworker_operable


class CanCaseworkersManageOrgainsation(permissions.BasePermission):
    def has_permission(self, request, view):
        return check_user_has_permission(request.user.govuser, GovPermissions.MANAGE_ORGANISATIONS)


class CanCaseworkersIssueLicence(permissions.BasePermission):
    def has_permission(self, request, view):
        return check_user_has_permission(request.user.govuser, GovPermissions.MANAGE_LICENCE_FINAL_ADVICE)


class CanCaseworkerBulkApprove(permissions.BasePermission):
    def has_permission(self, request, view):
        queue_pk = view.kwargs["pk"]
        return str(queue_pk) in BULK_APPROVE_ALLOWED_QUEUES
