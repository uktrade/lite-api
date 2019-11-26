from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication, SharedAuthentication
from conf.constants import Roles, Permissions
from conf.permissions import assert_user_has_permission
from gov_users.serializers import RoleSerializer, PermissionSerializer
from users.enums import UserType
from users.libraries.get_role import get_role_by_pk
from users.models import Role, Permission


class RolesViews(APIView):
    """
    Manage roles
    """

    authentication_classes = (SharedAuthentication,)

    def get(self, request):
        """
        Return list of all roles
        """
        roles = Role.objects.filter(type=UserType.INTERNAL).order_by("name")
        if request.user.role_id != Roles.INTERNAL_SUPER_USER_ROLE_ID:
            roles = roles.exclude(id=Roles.INTERNAL_SUPER_USER_ROLE_ID)
        serializer = RoleSerializer(roles, many=True)
        return JsonResponse(data={"roles": serializer.data})

    @swagger_auto_schema(request_body=RoleSerializer, responses={400: "JSON parse error"})
    def post(self, request):
        """
        Create a role
        """
        assert_user_has_permission(request.user, Permissions.ADMINISTER_ROLES)
        data = JSONParser().parse(request)
        data["type"] = UserType.INTERNAL

        if Role.objects.filter(organisation=None, name__iexact=data["name"].strip()):
            error = {"name": [ErrorDetail(string="Name is not unique.", code="invalid")]}
            return JsonResponse(data={"errors": error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RoleSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"role": serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class RoleDetail(APIView):
    """
    Manage a specific role
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Get the details of a specific role
        """
        role = get_role_by_pk(pk)
        serializer = RoleSerializer(role)

        return JsonResponse(data={"role": serializer.data})

    @swagger_auto_schema(request_body=RoleSerializer, responses={400: "JSON parse error"})
    def put(self, request, pk):
        """
        update a role
        """
        if pk == Roles.INTERNAL_SUPER_USER_ROLE_ID:
            return JsonResponse(
                data={"errors": "You cannot edit the super user role"}, status=status.HTTP_400_BAD_REQUEST,
            )

        assert_user_has_permission(request.user, Permissions.ADMINISTER_ROLES)

        data = JSONParser().parse(request)
        role = get_role_by_pk(pk)

        serializer = RoleSerializer(role, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"role": serializer.data}, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PermissionsView(APIView):
    """
    Manage permissions
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Return list of all permissions
        """
        roles = Permission.internal.all()
        serializer = PermissionSerializer(roles, many=True)
        return JsonResponse(data={"permissions": serializer.data})
