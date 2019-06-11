from rest_framework import authentication, exceptions

from users.models import User, UserStatuses


class PkAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        pk = request.META.get('HTTP_USER_ID')

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user with that ID')

        if user.status == UserStatuses.deactivated:
            raise exceptions.AuthenticationFailed('User has been deactivated')

        return user, None


class EmailAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        email = request.META.get('HTTP_USER_EMAIL')

        try:
            user = GovUser.objects.get(email=email)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user with that email')

        return user, None
