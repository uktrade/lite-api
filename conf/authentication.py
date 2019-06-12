from rest_framework import authentication, exceptions

from gov_users.enums import GovUserStatuses
from gov_users.models import GovUser
from users.models import User, UserStatuses


class PkAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        pk = request.META.get('HTTP_USER_ID')
        print('\n\n\n\n\n')
        print(request.headers)
        print(request.META)
        print('\n\n\n\n\n')

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user with that ID')

        if user.status == UserStatuses.deactivated:
            raise exceptions.PermissionDenied('User has been deactivated')

        return user, None


class EmailAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        email = request.META.get('HTTP_GOV_USER_EMAIL')
        print('\n\n\n\n\n')
        print(request.headers)
        print(request.META)
        print('\n\n\n\n\n')
        try:
            user = GovUser.objects.get(email=email)
        except GovUser.DoesNotExist:
            raise exceptions.PermissionDenied('No such user with that email')

        if user.status == GovUserStatuses.DEACTIVATED:
            raise exceptions.PermissionDenied('User has been deactivated')

        return user, None
