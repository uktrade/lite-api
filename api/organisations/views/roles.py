from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.generics import ListCreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from api.core.authentication import ExporterAuthentication
from api.core.constants import Roles, ExporterPermissions
from api.core.permissions import assert_user_has_permission
from api.gov_users.serializers import RoleSerializer, PermissionSerializer, RoleListSerializer
from api.organisations.libraries.get_organisation import get_request_user_organisation_id
from api.users.enums import UserType
from api.users.libraries.get_role import get_role_by_pk
from api.users.models import Role
from api.users.services import get_exporter_roles_by_organisation


class RolesViews(ListCreateAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = RoleListSerializer

    def get_queryset(self):
        return get_exporter_roles_by_organisation(self.request, self.kwargs.get("org_pk"))

    def post(self, request, org_pk):
        """
        Create a role
        """
        assert_user_has_permission(request.user.exporteruser, ExporterPermissions.EXPORTER_ADMINISTER_ROLES, org_pk)
        data = JSONParser().parse(request)
        data["organisation"] = str(org_pk)
        data["type"] = UserType.EXPORTER

if Role.objects.filter(organisation=org_pk, name__iexact=data["name"].strip()).exists():
    error = {"name": [ErrorDetail(string="Name is not unique.", code="invalid")]}
    return JsonResponse(data={"errors": error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RoleSerializer(data=data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return JsonResponse(data={"role": serializer.data}, status=status.HTTP_201_CREATED)


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

    def put(self, request, org_pk, pk):
        """
        update a role
        """
        if pk in Roles.IMMUTABLE_ROLES:
            return JsonResponse(
                data={"errors": "You cannot edit the super user role"}, status=status.HTTP_400_BAD_REQUEST
            )

        assert_user_has_permission(request.user.exporteruser, ExporterPermissions.EXPORTER_ADMINISTER_ROLES, org_pk)

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
        permissions = request.user.exporteruser.get_role(get_request_user_organisation_id(request)).permissions.values()
        serializer = PermissionSerializer(permissions, many=True)
        return JsonResponse(data={"permissions": serializer.data})
