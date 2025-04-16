from rest_framework import permissions

from api.cases.enums import CaseTypeSubTypeEnum
from api.core.constants import GovPermissions
from api.core.exceptions import PermissionDeniedError
from api.organisations.libraries.get_organisation import get_request_user_organisation
from api.organisations.models import Organisation
from api.users.models import GovUser
from api.staticdata.statuses.enums import CaseStatusEnum
from lite_routing.routing_rules_internal.enums import TeamIdEnum

from lite_routing.routing_rules_internal.enums import QueuesEnum

BULK_APPROVE_ALLOWED_QUEUES = {
    "MOD_CAPPROT": QueuesEnum.MOD_CAPPROT,
    "MOD_DI_DIRECT": QueuesEnum.MOD_DI_DIRECT,
    "MOD_DI_INDIRECT": QueuesEnum.MOD_DI_INDIRECT,
    "MOD_DSR": QueuesEnum.MOD_DSR,
    "MOD_DSTL": QueuesEnum.MOD_DSTL,
    "NCSC": QueuesEnum.NCSC,
}


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


class CanCaseworkerFinaliseF680(permissions.BasePermission):
    def has_permission(self, request, view):
        # TODO: this is a perfect candidate for a django rule - we should think about that
        case = view.get_case()
        if not case.case_type.sub_type == CaseTypeSubTypeEnum.F680:
            return False

        if case.status.status != CaseStatusEnum.UNDER_FINAL_REVIEW:
            return False

        if str(request.user.govuser.team_id) != TeamIdEnum.MOD_ECJU:
            return False

        return True


class CanCaseworkerBulkApprove(permissions.BasePermission):
    def has_permission(self, request, view):
        queue_pk = view.kwargs["pk"]
        return str(queue_pk) in BULK_APPROVE_ALLOWED_QUEUES.values()
