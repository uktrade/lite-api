from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from conf.serializers import response_serializer
from gov_users.serializers import RoleSerializer, PermissionSerializer
from users.models import Role, Permission


class Roles(APIView):
    """
    Manage roles
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Return list of all roles
        """
        roles = Role.objects.all().order_by('name')
        return response_serializer(RoleSerializer, obj=roles, many=True)

    @swagger_auto_schema(
        request_body=RoleSerializer,
        responses={
            400: 'JSON parse error'
        })
    def post(self, request):
        """
        Create a role
        """
        data = JSONParser().parse(request)
        return response_serializer(RoleSerializer, data=data, object_class=Role)


class RoleDetail(APIView):
    """
    Manage a specific role
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        """
        Get the details of a specific role
        """
        return response_serializer(RoleSerializer, pk=pk, object_class=Role)

    @swagger_auto_schema(
        request_body=RoleSerializer,
        responses={
            400: 'JSON parse error'
        })
    def put(self, request, pk):
        """
        update a role
        """
        data = JSONParser().parse(request)
        return response_serializer(RoleSerializer, data=data, pk=pk, object_class=Role, partial=True)


class Permissions(APIView):
    """
    Manage permissions
    """
    authentication_classes = (GovAuthentication,)

    def get(self, request):
        """
        Return list of all permissions
        """
        roles = Permission.objects.all().order_by('name')
        return response_serializer(PermissionSerializer, obj=roles, many=True, response_name='permissions')