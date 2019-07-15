from django.http import JsonResponse
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import GovAuthentication
from gov_users.serializers import RoleSerializer


class Roles(APIView):
    """
    Manage roles
    """
    authentication_classes = (GovAuthentication,)

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

        print(serializer.errors)
        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
