from rest_framework import permissions
from api.core.constants import Roles
from api.core.permissions import assert_user_in_role


class CanCaseworkersManageUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.data.get("default_queue") and len(request.data) < 2:
            return True
        else:
            return assert_user_in_role(request.user.govuser, Roles.INTERNAL_SUPER_USER_ROLE_ID)
