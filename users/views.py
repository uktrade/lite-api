from django.http.response import JsonResponse, Http404, HttpResponseForbidden
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from users.models import User
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

        user = None

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise Http404

        if not user.check_password(password):
            return HttpResponseForbidden()

        serializer = ViewUserSerializer(user)
        return JsonResponse(data={'user': serializer.data},
                            safe=False)


class UserDetail(APIView):
    permission_classes = (AllowAny,)
    """
    Get user from pk
    """
    def get_user_by_pk(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        user = self.get_user_by_pk(pk)

        serializer = ViewUserSerializer(user)
        return JsonResponse(data={'user': serializer.data},
                            safe=False)
