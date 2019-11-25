from django.http import JsonResponse, Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from conf.constants import Roles, Permissions
from conf.permissions import assert_user_has_permission
from organisations.libraries.get_organisation import get_organisation_by_pk
from users.libraries.get_user import get_users_from_organisation, get_user_by_pk
from users.models import ExporterUser
from users.serializers import (
    ExporterUserViewSerializer,
    ExporterUserCreateUpdateSerializer,
    UserOrganisationRelationshipSerializer,
)


class UsersList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk):
        """
        List all users from the specified organisation
        """
        organisation = get_organisation_by_pk(org_pk)
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, Permissions.ADMINISTER_USERS, org_pk)

        users = get_users_from_organisation(organisation)
        view_serializer = ExporterUserViewSerializer(users, many=True, context=org_pk)
        return JsonResponse(data={"users": view_serializer.data})

    @swagger_auto_schema(responses={400: "JSON parse error"})
    def post(self, request, org_pk):
        """
        Create an exporter user within the specified organisation
        """
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, Permissions.ADMINISTER_USERS, org_pk)
        data = JSONParser().parse(request)
        data["organisation"] = str(org_pk)
        serializer = ExporterUserCreateUpdateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"user": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    user = None
    user_relationship = None

    def dispatch(self, request, *args, **kwargs):
        self.user = get_user_by_pk(kwargs["user_pk"])
        organisation = get_organisation_by_pk(kwargs["org_pk"])

        # Set the user's status in that org
        self.user_relationship = organisation.get_user_relationship(self.user)
        self.user.status = self.user_relationship.status

        return super(UserDetail, self).dispatch(request, *args, **kwargs)

    def get(self, request, org_pk, user_pk):
        """
        Return a user from the specified organisation
        """
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, Permissions.ADMINISTER_USERS, org_pk)
        view_serializer = ExporterUserViewSerializer(self.user, context=org_pk)
        return JsonResponse(data={"user": view_serializer.data})

    def put(self, request, org_pk, user_pk):
        """
        Update the status of a user
        """
        if isinstance(request.user, ExporterUser):
            assert_user_has_permission(request.user, Permissions.ADMINISTER_USERS, org_pk)
        data = JSONParser().parse(request)
        user = get_user_by_pk(user_pk)

        # Cannot perform actions on another super user without super user role
        if (
            user.get_role(org_pk).id == Roles.EXPORTER_SUPER_USER_ROLE_ID
            or data.get("role") == Roles.EXPORTER_SUPER_USER_ROLE_ID
        ) and not request.user.get_role(org_pk).id == Roles.EXPORTER_SUPER_USER_ROLE_ID:
            raise PermissionDenied()

        # Don't allow a user to update their own status or that of a super user
        if "status" in data.keys():
            if user.id == request.user.id:
                return JsonResponse(
                    data={"errors": "A user cannot change their own status"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif (
                user.get_role(org_pk).id == Roles.EXPORTER_SUPER_USER_ROLE_ID
                and data["status"] == "Deactivated"
            ):
                raise PermissionDenied()

        # Cannot remove super user from yourself
        if "role" in data.keys():
            if (
                user.id == request.user.id
                and request.user.get_role(org_pk).id == Roles.EXPORTER_SUPER_USER_ROLE_ID
            ):
                return JsonResponse(
                    data={"errors": "A user cannot remove super user from themselves"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = UserOrganisationRelationshipSerializer(instance=self.user_relationship, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"user_relationship": serializer.data})

        return JsonResponse(data={"errors": serializer.errors})
