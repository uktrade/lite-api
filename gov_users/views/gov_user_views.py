import reversion
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from gov_users.enums import GovUserStatuses
from gov_users.libraries.get_gov_user import get_gov_user_by_pk
from gov_users.libraries.user_to_token import user_to_token
from gov_users.serializers import GovUserCreateSerializer, GovUserViewSerializer
from users.libraries.user_is_trying_to_change_own_status import user_is_trying_to_change_own_status
from users.models import GovUser


class AuthenticateGovUser(APIView):
    """
    Authenticate user
    """
    permission_classes = (AllowAny,)

    @swagger_auto_schema(
        responses={
            400: 'JSON parse error',
            403: 'Forbidden'
        })
    def post(self, request, *args, **kwargs):
        """
        Takes user details from sso and checks them against our whitelisted users
        Returns a token which is just our ID for the user
        :param request:
        :param email, first_name, last_name:
        :return token:
        """
        try:
            data = JSONParser().parse(request)
        except ParseError:
            return JsonResponse(data={'errors': 'Invalid Json'},
                                status=status.HTTP_400_BAD_REQUEST)
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
        return JsonResponse(data={'token': token, 'lite_api_user_id': str(user.id)})


class GovUserList(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Fetches all government users
        """
        teams = request.GET.get('teams', None)

        if teams:
            gov_users = GovUser.objects.filter(team__id__in=teams.split(',')).order_by('email')
        else:
            gov_users = GovUser.objects.all().order_by('email')

        serializer = GovUserViewSerializer(gov_users, many=True)
        return JsonResponse(data={'gov_users': serializer.data})

    @swagger_auto_schema(
        request_body=GovUserCreateSerializer,
        responses={
            400: 'JSON parse error'
        })
    def post(self, request):
        """
        Add a new gov user
        """
        data = JSONParser().parse(request)
        serializer = GovUserCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'gov_user': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class GovUserDetail(APIView):
    """
    Actions on a specific user
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Get user from pk
        """
        gov_user = get_gov_user_by_pk(pk)

        serializer = GovUserViewSerializer(gov_user)
        return JsonResponse(data={'user': serializer.data})

    @swagger_auto_schema(
        request_body=GovUserCreateSerializer,
        responses={
            400: 'Bad Request'
        })
    def put(self, request, pk):
        """
        Edit user from pk
        """
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

            serializer = GovUserCreateSerializer(gov_user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()

                # Remove user from assigned cases
                if gov_user.status == GovUserStatuses.DEACTIVATED:
                    gov_user.unassign_from_cases()

                return JsonResponse(data={'gov_user': serializer.data},
                                    status=status.HTTP_200_OK)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)


class UserMeDetail(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Get the user from request
    """
    def get(self, request):
        serializer = GovUserViewSerializer(request.user)
        return JsonResponse(data={'user': serializer.data})
