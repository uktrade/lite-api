from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.serializers import response_serializer
from gov_users.enums import GovUserStatuses
from gov_users.serializers import GovUserCreateSerializer, GovUserViewSerializer
from users.helpers import bad_request_if_user_edit_own_status, unassign_from_cases
from users.libraries.user_to_token import user_to_token
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

        return response_serializer(GovUserViewSerializer, obj=gov_users, many=True)

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
        return response_serializer(GovUserCreateSerializer, data=data, response_name='gov_user')


class GovUserDetail(APIView):
    """
    Actions on a specific user
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Get user from pk
        """
        return response_serializer(GovUserViewSerializer, pk=pk, object_class=GovUser)

    @swagger_auto_schema(
        request_body=GovUserCreateSerializer,
        responses={
            400: 'Bad Request'
        })
    def put(self, request, pk):
        """
        Edit user from pk
        """
        data = JSONParser().parse(request)
        return response_serializer(GovUserCreateSerializer,
                                   pk=pk,
                                   object_class=GovUser,
                                   request=request,
                                   data=data,
                                   pre_validation_actions=[bad_request_if_user_edit_own_status],
                                   post_save_actions=[unassign_from_cases],
                                   partial=True,
                                   response_name='gov_user')


class UserMeDetail(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Get the user from request
    """
    def get(self, request):
        serializer = GovUserViewSerializer(request.user)
        return JsonResponse(data={'user': serializer.data})
