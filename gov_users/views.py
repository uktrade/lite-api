import reversion
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from conf.authentication import EmailAuthentication
from gov_users.enums import GovUserStatuses
from gov_users.libraries.get_gov_user import get_gov_user_by_pk
from gov_users.libraries.user_to_token import user_to_token
from gov_users.models import GovUser
from gov_users.serializers import GovUserSerializer
from users.libraries.user_is_trying_to_change_own_status import user_is_trying_to_change_own_status


class AuthenticateGovUser(APIView):
    permission_classes = (AllowAny,)
    """
    Authenticate user
    """
    def post(self, request, *args, **kwargs):
        data = JSONParser().parse(request)
        email = data.get('email')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        try:
            user = GovUser.objects.get(email=email)

            # Update the user's first and last names
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        except GovUser.DoesNotExist:
            return JsonResponse(data={'errors': 'User not found'},
                                status=status.HTTP_403_FORBIDDEN)

        if user.status == GovUserStatuses.DEACTIVATED:
            return JsonResponse(data={'errors': 'User not found'},
                                status=status.HTTP_403_FORBIDDEN)

        token = user_to_token(user)
        return JsonResponse(data={'token': token})


class GovUserList(APIView):
    authentication_classes = (EmailAuthentication,)

    def get(self, request):
        serializer = GovUserSerializer(GovUser.objects.all(), many=True)
        return JsonResponse(data={'gov_users': serializer.data}, safe=False)

    def post(self, request):

        data = JSONParser().parse(request)
        serializer = GovUserSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'good': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class GovUserDetail(APIView):
    authentication_classes = (EmailAuthentication,)
    """
    Get user from pk
    """
    def get(self, request, pk):
        gov_user = get_gov_user_by_pk(pk)

        serializer = GovUserSerializer(gov_user)
        return JsonResponse(data={'user': serializer.data},
                            safe=False)

    def put(self, request, pk):
        gov_user = get_gov_user_by_pk(pk)
        data = JSONParser().parse(request)
        if 'status' in data.keys():
            if user_is_trying_to_change_own_status(gov_user.id, GovUser.objects.get(email=request.user.email).id):
                return JsonResponse(data={'errors': 'A user cannot change their own status'},
                                    status=status.HTTP_400_BAD_REQUEST)
        with reversion.create_revision():

            for key in list(data.keys()):
                if data[key] is '':
                    del data[key]

            serializer = GovUserSerializer(gov_user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(data={'gov_user': serializer.data},
                                    status=status.HTTP_200_OK)
            print(serializer.errors)
            return JsonResponse(data={'errors': serializer.errors},
                                status=400)
