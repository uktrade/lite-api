from django.http.response import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from users.libraries.get_user import get_user_by_pk, get_user_by_email
from users.serializers import ViewUserSerializer


class AuthenticateUser(APIView):
    permission_classes = (AllowAny,)
    """
    Authenticate user
    """
    def post(self, request, *args, **kwargs):
        data = JSONParser().parse(request)

        email = data.get('email')
        password = data.get('password')

        user = get_user_by_email(email)

        if not user.check_password(password):
            return JsonResponse(data={'errors': 'Incorrect password'},
                                status=status.HTTP_401_UNAUTHORIZED,
                                safe=False)

        serializer = ViewUserSerializer(user)
        return JsonResponse(data={'user': serializer.data},
                            safe=False)


class UserDetail(APIView):
    authentication_classes = (PkAuthentication,)
    """
    Get user from pk
    """
    def get(self, request, pk):
        user = get_user_by_pk(pk)

        serializer = ViewUserSerializer(user)
        return JsonResponse(data={'user': serializer.data},
                            safe=False)
