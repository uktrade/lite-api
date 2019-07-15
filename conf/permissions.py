from rest_framework import exceptions

from gov_users.models import Permission
from users.models import User


class CanMakeFinalDecisions:
    def check_permissions(self, request):
        pk = request.META.get('HTTP_USER_ID')
        user = User.objects.get(pk=pk)

        if Permission.objects.get(id='00000000-0000-0000-0000-000000000001') not in user.role.permissions:
            raise exceptions.PermissionDenied('User does not have permission to make final decisions')

        return None
