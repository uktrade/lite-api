from rest_framework import authentication, exceptions

from gov_users.enums import GovUserStatuses
from gov_users.libraries.token_to_user_pk import token_to_user_pk
from gov_users.models import GovUser
from users.models import User, UserStatuses


class PkAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        pk = request.META.get('HTTP_USER_ID')
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user with that ID')

        if user.status == UserStatuses.DEACTIVATED:
            raise exceptions.PermissionDenied('User has been deactivated')

        return user, None