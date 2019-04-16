
from django.http.response import JsonResponse, Http404
from oauth2_provider.views import ProtectedResourceView
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from users.models import User
from users.serializers import ViewUserSerializer


@permission_classes((permissions.AllowAny,))
class UserList(APIView):
    """
    Get all users
    """
    def get(self, request):
        users = User.objects.all()
        serializer = ViewUserSerializer(users, many=True)
        return JsonResponse(data={'users': serializer.data},
                            safe=False)


class UserMeDetail(ProtectedResourceView):
    """
    Get user from token
    """
    def get(self, request, *args, **kwargs):
        user = User.objects.get(email=request.user)

        serializer = ViewUserSerializer(user)
        return JsonResponse(data={'user': serializer.data},
                            safe=False)


@permission_classes((permissions.AllowAny,))
class UserDetail(APIView):
    """
    Get user from pk
    """
    def get_object(self, pk):
        try:
            user = User.objects.get(pk=pk)
            return user
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        user = self.get_object(pk)

        serializer = ViewUserSerializer(user)
        return JsonResponse(data={'user': serializer.data},
                            safe=False)
