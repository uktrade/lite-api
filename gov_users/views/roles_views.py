from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from gov_users.libraries.get_role import get_role_by_pk
from gov_users.models import Role, Permission
from gov_users.serializers import RoleSerializer, PermissionSerializer


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
        serializer = RoleSerializer(roles, many=True)
        return JsonResponse(data={'roles': serializer.data})

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

        serializer = RoleSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'role': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


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

        return JsonResponse(data={'role': serializer.data})

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
        role = get_role_by_pk(pk)

        serializer = RoleSerializer(role, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'role': serializer.data},
                                status=status.HTTP_200_OK)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


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
        serializer = PermissionSerializer(roles, many=True)
        return JsonResponse(data={'permissions': serializer.data})