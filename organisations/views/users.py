from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from conf.constants import Roles, ExporterPermissions
from conf.permissions import assert_user_has_permission
from lite_content.lite_api import strings
from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.serializers import OrganisationUserListView
from users.libraries.get_user import get_user_by_pk, get_user_organisation_relationships
from users.models import ExporterUser, Role
from users.serializers import (
    ExporterUserViewSerializer,
    ExporterUserCreateUpdateSerializer,
    UserOrganisationRelationshipSerializer,
)
from users.services import filter_roles_by_user_role


class UsersList(generics.ListCreateAPIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk):
        """
        List all users from the specified organisation
        """
        status = request.GET.get("status")

        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, ExporterPermissions.ADMINISTER_USERS, org_pk)

        user_relationships = get_user_organisation_relationships(org_pk, status)
        page = self.paginate_queryset(user_relationships)

        for p in page:
            p.user.status = p.status
            p.user.role = p.role

        serializer = OrganisationUserListView([p.user for p in page], many=True)

        return self.get_paginated_response({
            "users": serializer.data,
            "filters": {"status": [{"key": "active", "value": "Active"}, {"key": "", "value": "All"}]}
        })

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
            exporter_roles = [str(role) for role in Roles.EXPORTER_PRESET_ROLES]
            user_roles = [
                str(role.id)
                for role in filter_roles_by_user_role(request.user, Role.objects.filter(organisation=org_pk), org_pk)
            ]
            if data["role"] not in exporter_roles + user_roles:
                raise PermissionDenied()

        serializer = UserOrganisationRelationshipSerializer(instance=user_relationship, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"user_relationship": serializer.data})

        return JsonResponse(data={"errors": serializer.errors})
