from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from organisations.libraries.get_organisation import get_organisation_by_pk
from users.libraries.get_user import get_users_from_organisation
from users.serializers import ExporterUserViewSerializer, ExporterUserCreateUpdateSerializer


class UsersList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk):
        """
        List all users from the specified organisation
        """
        organisation = get_organisation_by_pk(org_pk)

        users = get_users_from_organisation(organisation)
        view_serializer = ExporterUserViewSerializer(users, many=True)
        return JsonResponse(data={'users': view_serializer.data})

    @swagger_auto_schema(
        responses={
            400: 'JSON parse error'
        })
    def post(self, request, org_pk):
        """
        Create an exporter user within the specified organisation
        """
        data = JSONParser().parse(request)
        data['organisation'] = str(org_pk)
        serializer = ExporterUserCreateUpdateSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data={'user': serializer.data},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)
