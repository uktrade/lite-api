from django.db.models import Value
from django.db.models.functions import Concat
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.constants import Roles
from conf.helpers import replace_default_string_for_form_select
from gov_users.enums import GovUserStatuses
from gov_users.serializers import GovUserCreateSerializer, GovUserViewSerializer
from users.enums import UserStatuses
from users.libraries.get_user import get_user_by_pk
from users.libraries.user_to_token import user_to_token
from users.models import GovUser, GovNotification


class AuthenticateGovUser(APIView):
    """
    Authenticate user
    """

    permission_classes = (AllowAny,)

    @swagger_auto_schema(responses={400: "JSON parse error", 403: "Forbidden"})
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
            return JsonResponse(data={"errors": "Invalid Json"}, status=status.HTTP_400_BAD_REQUEST)
        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")

        try:
            user = GovUser.objects.get(email=email)

            # Update the user's first and last names
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        except GovUser.DoesNotExist:
            return JsonResponse(data={"errors": "User not found"}, status=status.HTTP_403_FORBIDDEN)

        if user.status == GovUserStatuses.DEACTIVATED:
            return JsonResponse(data={"errors": "User not found"}, status=status.HTTP_403_FORBIDDEN)

        token = user_to_token(user)
        return JsonResponse(data={"token": token, "lite_api_user_id": str(user.id)})


class GovUserList(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Fetches all government users
        """
        teams = request.GET.get("teams", None)
        activated_only = request.GET.get("activated", None)
        full_name = request.GET.get("name", None)

        gov_users_qs = GovUser.objects.all()

        if activated_only:
            gov_users_qs = gov_users_qs.exclude(status=UserStatuses.DEACTIVATED)

        if full_name:
            gov_users_qs = gov_users_qs.annotate(full_name=Concat("first_name", Value(" "), "last_name")).filter(
                full_name__icontains=full_name
            )

        if teams:
            gov_users_qs = gov_users_qs.filter(team__id__in=teams.split(","))

        serializer = GovUserViewSerializer(gov_users_qs, many=True)
        return JsonResponse(data={"gov_users": serializer.data})

    @swagger_auto_schema(request_body=GovUserCreateSerializer, responses={400: "JSON parse error"})
    def post(self, request):
        """
        Add a new gov user
        """
        data = JSONParser().parse(request)
        data = replace_default_string_for_form_select(data, fields=["role", "team"])

        if (
            data.get("role") == str(Roles.INTERNAL_SUPER_USER_ROLE_ID)
            and not request.user.role_id == Roles.INTERNAL_SUPER_USER_ROLE_ID
        ):
            raise PermissionDenied()

        serializer = GovUserCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"gov_user": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class GovUserDetail(APIView):
    """
    Actions on a specific user
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Get user from pk
        """
        gov_user = get_user_by_pk(pk)

        serializer = GovUserViewSerializer(gov_user)
        return JsonResponse(data={"user": serializer.data})

    @swagger_auto_schema(request_body=GovUserCreateSerializer, responses={400: "Bad Request"})
    def put(self, request, pk):
        """
        Edit user from pk
        """
        gov_user = get_user_by_pk(pk)
        data = JSONParser().parse(request)

        # Cannot perform actions on another super user without super user role
        if (
            gov_user.role_id == Roles.INTERNAL_SUPER_USER_ROLE_ID
            or data.get("roles") == Roles.INTERNAL_SUPER_USER_ROLE_ID
        ) and not request.user.role_id == Roles.INTERNAL_SUPER_USER_ROLE_ID:
            raise PermissionDenied()

        if "status" in data.keys():
            if gov_user.id == request.user.id:
                return JsonResponse(
                    data={"errors": "A user cannot change their own status"}, status=status.HTTP_400_BAD_REQUEST,
                )
            elif gov_user.role_id == Roles.INTERNAL_SUPER_USER_ROLE_ID and data["status"] == "Deactivated":
                raise PermissionDenied()

        # Cannot deactivate a super user
        if "role" in data.keys():
            if gov_user.id == request.user.id and request.user.role_id == Roles.INTERNAL_SUPER_USER_ROLE_ID:
                return JsonResponse(
                    data={"errors": "A user cannot remove super user from themselves"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        data = replace_default_string_for_form_select(data, fields=["role", "team"])

        serializer = GovUserCreateSerializer(gov_user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Remove user from assigned cases
            if gov_user.status == GovUserStatuses.DEACTIVATED:
                gov_user.unassign_from_cases()

            return JsonResponse(data={"gov_user": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserMeDetail(APIView):
    authentication_classes = (GovAuthentication,)
    """
    Get the user from request
    """

    def get(self, request):
        serializer = GovUserViewSerializer(request.user)
        return JsonResponse(data={"user": serializer.data})


class NotificationViewSet(APIView):
    authentication_classes = (GovAuthentication,)
    queryset = GovNotification.objects.all()

    # TODO: LT-1180 endpoint
    def get(self, request):

        return JsonResponse(data={"notifications": []}, status=status.HTTP_200_OK)
