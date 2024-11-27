from rest_framework import permissions
from api.core.constants import Roles
from api.core.permissions import assert_user_in_role


class CanCaseworkersManageUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return assert_user_in_role(request.user.govuser, Roles.INTERNAL_SUPER_USER_ROLE_ID)


class CanUserManageQueue(permissions.BasePermission):
    def has_permission(self, request, view):
        user_managing_self = request.user.govuser.pk == view.kwargs["pk"]
        user_managing_queue = list(request.data.keys()) == ["default_queue"]
        return user_managing_self and user_managing_queue
