import reversion
from django.http.response import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from conf.authentication import PkAuthentication
from organisations.libraries.get_organisation import get_organisation_by_user
from users.libraries.get_user import get_user_by_pk, get_user_by_email
from users.libraries.user_is_trying_to_change_own_status import user_is_trying_to_change_own_status
from users.models import User, UserStatuses
from users.serializers import UserViewSerializer, UserUpdateSerializer, UserCreateSerializer


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
        if user.status == UserStatuses.deactivated:
            return JsonResponse(data={},
                                status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return JsonResponse(data={},
                                status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserViewSerializer(user)
        return JsonResponse(data={'user': serializer.data},
                            safe=False)


class UserList(APIView):
    authentication_classes = (PkAuthentication,)

    def get(self, request):
        organisation = get_organisation_by_user(request.user)
        serializer = UserViewSerializer(User.objects.filter(organisation=organisation), many=True)
        return JsonResponse(data={'users': serializer.data}, safe=False)

    def post(self, request):
        organisation = get_organisation_by_user(request.user)

        data = JSONParser().parse(request)
        data['organisation'] = organisation.id
        serializer = UserCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'good': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    authentication_classes = (PkAuthentication,)
    """
    Get user from pk
    """
    def get(self, request, pk):
        user = get_user_by_pk(pk)

        serializer = UserViewSerializer(user)
        return JsonResponse(data={'user': serializer.data},
                            safe=False)

    def put(self, request, pk):
        user = get_user_by_pk(pk)
        data = JSONParser().parse(request)
        if 'status' in data.keys():
            if user_is_trying_to_change_own_status(user.id, request.user.id):
                return JsonResponse(data={'errors': 'A user cannot change their own status'},
                                    status=status.HTTP_400_BAD_REQUEST)
        with reversion.create_revision():

            for key in list(data.keys()):
                if data[key] is '':
                    del data[key]

            serializer = UserUpdateSerializer(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(data={'user': serializer.data},
                                    status=status.HTTP_200_OK)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)
