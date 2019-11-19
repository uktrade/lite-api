from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication, ExporterAuthentication
from conf.constants import Roles, Permissions
from conf.permissions import assert_user_has_permission
from gov_users.serializers import RoleSerializer, PermissionSerializer
from users.libraries.get_role import get_role_by_pk


class RolesViews(APIView):
    """
    Manage roles
    """

    authentication_classes = (ExporterAuthentication,)

    def get(self, request, org_pk):
        """
        Return list of all roles
        """
        roles = [x for x in Role.objects.filter(organisation=org_pk)]
        roles.append(Role.objects.get(id=Roles.EXPORTER_DEFAULT_ROLE_ID))
        if request.user.get_role(org_pk).id == Roles.EXPORTER_SUPER_USER_ROLE_ID:
            roles.append(Role.objects.get(id=Roles.EXPORTER_SUPER_USER_ROLE_ID))
        serializer = RoleSerializer(roles, many=True)
        return JsonResponse(data={"roles": serializer.data})

    @swagger_auto_schema(
        request_body=RoleSerializer, responses={400: "JSON parse error"}
    )
    def post(self, request, org_pk):
        """
        Create a role
        """
        assert_user_has_permission(request.user, Permissions.EXPORTER_ADMINISTER_ROLES, org_pk)
        data = JSONParser().parse(request)

        serializer = RoleSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(
                data={"role": serializer.data}, status=status.HTTP_201_CREATED
            )

        return JsonResponse(
            data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )


class RoleDetail(APIView):
    """
    Manage a specific role
    """

    authentication_classes = (ExporterAuthentication,)

    def get(self, request, org_pk, pk):
        """
        Get the details of a specific role
        """

        role = get_role_by_pk(pk, org_pk)
        serializer = RoleSerializer(role)

        return JsonResponse(data={"role": serializer.data})

    @swagger_auto_schema(
        request_body=RoleSerializer, responses={400: "JSON parse error"}
    )
    def put(self, request, org_pk, pk):
        """
        update a role
        """
        if pk == Roles.EXPORTER_SUPER_USER_ROLE_ID:
            return JsonResponse(
                data={"errors": "You cannot edit the super user role"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assert_user_has_permission(request.user, Permissions.EXPORTER_ADMINISTER_ROLES, org_pk)

        data = JSONParser().parse(request)
        role = get_role_by_pk(pk, org_pk)

        serializer = RoleSerializer(role, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(
                data={"role": serializer.data}, status=status.HTTP_200_OK
            )

        return JsonResponse(
            data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )


class PermissionsView(APIView):
    """
    Manage permissions
    """

    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        Return list of all permissions
        """
        roles = Permission.objects.all().order_by("name")
        serializer = PermissionSerializer(roles, many=True)
        return JsonResponse(data={"permissions": serializer.data})
