from rest_framework import authentication, exceptions

from users.models import User


class PkAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        pk = request.META.get('HTTP_USER_ID')

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user with that ID')

        return user, None
