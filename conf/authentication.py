from rest_framework import authentication, exceptions
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser

from users.models import User


class PkAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        try:
            data = JSONParser().parse(request)
        except ParseError:
            raise exceptions.AuthenticationFailed('Invalid JSON request')

        pk = data.get('id')

        if 'id' not in data:
            raise exceptions.AuthenticationFailed('Missing ID in JSON body')

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user with that ID')

        return user, None
