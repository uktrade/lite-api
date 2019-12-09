from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.generics import ListCreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from conf.constants import Roles, ExporterPermissions
from conf.permissions import assert_user_has_permission
from gov_users.serializers import RoleSerializer, PermissionSerializer
from users.enums import UserType
from users.libraries.get_role import get_role_by_pk
from users.models import Role
from users.services import get_exporter_roles_by_organisation


class RolesViews(ListCreateAPIView):

    authentication_classes = (ExporterAuthentication,)

    serializer_class = RoleSerializer

    def get_queryset(self):
        return get_exporter_roles_by_organisation(self.request, self.kwargs.get("org_pk"))

    @swagger_auto_schema(request_body=RoleSerializer, responses={400: "JSON parse error"})
    def post(self, request, org_pk):
        """
        Create a role
        """
        assert_user_has_permission(request.user, ExporterPermissions.EXPORTER_ADMINISTER_ROLES, org_pk)
        data = JSONParser().parse(request)
        data["organisation"] = str(org_pk)
        data["type"] = UserType.EXPORTER

        if Role.objects.filter(organisation=org_pk, name__iexact=data["name"].strip()):
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

    authentication_classes = (ExporterAuthentication,)

    def get(self, request, org_pk, pk):
        """
        Get the details of a specific role
        """

        role = get_role_by_pk(pk, org_pk)
        serializer = RoleSerializer(role)

        return JsonResponse(data={"role": serializer.data})

    @swagger_auto_schema(request_body=RoleSerializer, responses={400: "JSON parse error"})
    def put(self, request, org_pk, pk):
        """
        update a role
        """
        if pk in Roles.IMMUTABLE_ROLES:
            return JsonResponse(
                data={"errors": "You cannot edit the super user role"}, status=status.HTTP_400_BAD_REQUEST
            )

        assert_user_has_permission(request.user, ExporterPermissions.EXPORTER_ADMINISTER_ROLES, org_pk)

        data = JSONParser().parse(request)
        role = get_role_by_pk(pk, org_pk)

        serializer = RoleSerializer(role, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={"role": serializer.data}, status=status.HTTP_200_OK)
        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PermissionsView(APIView):
    """
    Manage permissions
    """

    authentication_classes = (ExporterAuthentication,)

    def get(self, request):
        """
        Return list of all permissions
        """
        permissions = request.user.get_role(request.headers["Organisation-Id"]).permissions.values()
        serializer = PermissionSerializer(permissions, many=True)
        return JsonResponse(data={"permissions": serializer.data})
