import logging

from django.http import JsonResponse

from rest_framework import status, generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from api.core.authentication import GovAuthentication, HawkOnlyAuthentication
from api.core.constants import Roles, GovPermissions
from api.core.custom_views import OptionalPaginationView
from api.gov_users.enums import GovUserStatuses
from api.gov_users.serializers import GovUserCreateOrUpdateSerializer, GovUserViewSerializer, GovUserListSerializer
from api.organisations.enums import OrganisationStatus
from api.organisations.models import Organisation
from api.users.enums import UserStatuses
from api.users.libraries.get_user import get_user_by_pk
from api.users.libraries.user_to_token import user_to_token
from api.users.models import GovUser


logger = logging.getLogger(__name__)


class AuthenticateGovUser(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def post(self, request, *args, **kwargs):
        """
        Takes user details from sso and checks them against our whitelisted users
        Returns a token which is just our ID for the user
        :param request:
        :param email, first_name, last_name:
        :return token:
        """
        data = request.data
        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")

        logger.info("Authenticating user: %s payload: %s", email, data)
        try:
            user = GovUser.objects.get(baseuser_ptr__email=email)
        except GovUser.DoesNotExist:
            logger.info("User not found: %s", email)
            return JsonResponse(data={"errors": "User not found"}, status=status.HTTP_403_FORBIDDEN)

        if first_name and last_name:
            # Update the user's first and last names
            user.baseuser_ptr.first_name = first_name
            user.baseuser_ptr.last_name = last_name
            user.baseuser_ptr.pending = False
            user.baseuser_ptr.save()

        if user.status == GovUserStatuses.DEACTIVATED:
            logger.info("User deactivated: %s", email)
            return JsonResponse(data={"errors": "User not found"}, status=status.HTTP_403_FORBIDDEN)

        token = user_to_token(user.baseuser_ptr)
        return JsonResponse(
            data={"default_queue": str(user.default_queue), "token": token, "lite_api_user_id": str(user.pk)}
        )


class GovUserList(OptionalPaginationView, generics.CreateAPIView):
    authentication_classes = (GovAuthentication,)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return GovUserListSerializer
        else:
            return GovUserViewSerializer

    def get_queryset(self):
        gov_users_qs = GovUser.objects.all().order_by("baseuser_ptr__email").prefetch_related("team", "role")
        teams = self.request.GET.get("teams")
        status = self.request.GET.get("status")
        email = self.request.GET.get("email")

        if status:
            gov_users_qs = gov_users_qs.filter(status=UserStatuses.from_string(status))
        if teams:
            gov_users_qs = gov_users_qs.filter(team__id__in=teams.split(","))
        if email:
            gov_users_qs = gov_users_qs.filter(baseuser_ptr__email__icontains=email)

        return gov_users_qs

    def post(self, request):
        """
        Add a new gov user
        """

        if (
            request.data.get("role") == str(Roles.INTERNAL_SUPER_USER_ROLE_ID)
            and not request.user.govuser.role_id == Roles.INTERNAL_SUPER_USER_ROLE_ID
        ):
            raise PermissionDenied()

        serializer = GovUserCreateOrUpdateSerializer(data=request.data, is_creating=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"gov_user": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class GovUserDetail(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Get user from pk
        """
        gov_user = get_user_by_pk(pk)

        serializer = GovUserViewSerializer(gov_user)
        return JsonResponse(data={"user": serializer.data})

    def put(self, request, pk):
        """
        Edit user from pk
        """
        gov_user = get_user_by_pk(pk)
        data = request.data

        # Cannot perform actions on another super user without super user role
        if (
            gov_user.role_id == Roles.INTERNAL_SUPER_USER_ROLE_ID
            or data.get("roles") == Roles.INTERNAL_SUPER_USER_ROLE_ID
        ) and not request.user.govuser.role_id == Roles.INTERNAL_SUPER_USER_ROLE_ID:
            raise PermissionDenied()

        if "status" in data.keys():
            if gov_user.pk == request.user.pk:
                return JsonResponse(
                    data={"errors": "A user cannot change their own status"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif gov_user.role_id == Roles.INTERNAL_SUPER_USER_ROLE_ID and data["status"] == "Deactivated":
                raise PermissionDenied()

        # Cannot deactivate a super user
        if "role" in data.keys():
            if gov_user.pk == request.user.pk and request.user.govuser.role_id == Roles.INTERNAL_SUPER_USER_ROLE_ID:
                return JsonResponse(
                    data={"errors": "A user cannot remove super user from themselves"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = GovUserCreateOrUpdateSerializer(gov_user, data=data, partial=True, is_creating=False)
        if serializer.is_valid():
            serializer.save()

            # Remove user from assigned cases
            if gov_user.status == GovUserStatuses.DEACTIVATED:
                gov_user.unassign_from_cases()

            return JsonResponse(data={"gov_user": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserMeDetail(APIView):
    """
    Get the user from request
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request):
        serializer = GovUserViewSerializer(request.user.govuser)
        return JsonResponse(data={"user": serializer.data}, status=status.HTTP_200_OK)


class Notifications(APIView):
    """
    Get notifications for a gov user (seen in the menu)
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request):
        notifications = {
            "organisations": Organisation.objects.filter(status=OrganisationStatus.IN_REVIEW).count()
            if request.user.govuser.has_permission(GovPermissions.MANAGE_ORGANISATIONS)
            else 0
        }
        return JsonResponse(
            {"notifications": notifications, "has_notifications": any(value for value in notifications.values())}
        )
