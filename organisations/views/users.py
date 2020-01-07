from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from conf.constants import Roles, ExporterPermissions
from conf.permissions import assert_user_has_permission
from lite_content.lite_api import strings
from organisations.libraries.get_organisation import get_organisation_by_pk
from users.libraries.get_user import get_users_from_organisation, get_user_by_pk
from users.models import ExporterUser, Role
from users.serializers import (
    ExporterUserViewSerializer,
    ExporterUserCreateUpdateSerializer,
    UserOrganisationRelationshipSerializer,
)
from users.services import filter_roles_by_user_role


class UsersList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk):
        """
        List all users from the specified organisation
        """
        organisation = get_organisation_by_pk(org_pk)
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_USERS, org_pk)

        users = get_users_from_organisation(organisation)
        view_serializer = ExporterUserViewSerializer(users, many=True, context=org_pk)
        return JsonResponse(data={"users": view_serializer.data})

    @swagger_auto_schema(responses={400: "JSON parse error"})
    def post(self, request, org_pk):
        """
        Create an exporter user within the specified organisation
        """
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_USERS, org_pk)
        data = JSONParser().parse(request)
        data["organisation"] = str(org_pk)
        serializer = ExporterUserCreateUpdateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"user": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk, user_pk):
        """
        Return a user from the specified organisation
        """
        is_self = str(request.user.id) == str(user_pk)
        if not is_self and isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_USERS, org_pk)

        user = get_user_by_pk(user_pk)
        org = get_organisation_by_pk(org_pk)

        # Set the user's status in that org
        user_relationship = org.get_user_relationship(user)
        user.status = user_relationship.status

        view_serializer = ExporterUserViewSerializer(user, context=org_pk)
        return JsonResponse(data={"user": view_serializer.data})

    def put(self, request, org_pk, user_pk):
        """
        Update the status of a user
        """
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_USERS, org_pk)

        data = JSONParser().parse(request)
        user = get_user_by_pk(user_pk)
        org = get_organisation_by_pk(org_pk)

        # Set the user's status in that org
        user_relationship = org.get_user_relationship(user)
        user.status = user_relationship.status

        # Cannot perform actions on another super user without super user role
        if (
            data.get("role") == Roles.EXPORTER_SUPER_USER_ROLE_ID
            or user.get_role(org_pk).id == Roles.EXPORTER_SUPER_USER_ROLE_ID
        ) and not request.user.get_role(org_pk).id == Roles.EXPORTER_SUPER_USER_ROLE_ID:
            raise PermissionDenied()

        # Don't allow a user to update their own status or that of a super user
        if "status" in data.keys():
            if user.id == request.user.id:
                return JsonResponse(
                    data={"errors": "A user cannot change their own status"}, status=status.HTTP_400_BAD_REQUEST
                )
            elif user.get_role(org_pk).id == Roles.EXPORTER_SUPER_USER_ROLE_ID and data["status"] == "Deactivated":
                raise PermissionDenied()

        # Cannot remove super user from yourself
        if "role" in data.keys():
            if user.id == request.user.id:
                return JsonResponse(
                    data={"errors": strings.Users.ORGANISATIONS_VIEWS_USER_CANNOT_CHANGE_OWN_ROLE},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif user.id == request.user.id and request.user.get_role(org_pk).id == Roles.EXPORTER_SUPER_USER_ROLE_ID:
                return JsonResponse(
                    data={"errors": "A user cannot remove super user from themselves"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Cannot assign a role, you do not have access to
            if data["role"] not in str(Roles.EXPORTER_PRESET_ROLES) and data["role"] not in filter_roles_by_user_role(
                request.user, Role.objects.filter(organisation=org_pk), org_pk
            ):
                raise PermissionDenied()

        serializer = UserOrganisationRelationshipSerializer(instance=user_relationship, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"user_relationship": serializer.data})

        return JsonResponse(data={"errors": serializer.errors})
