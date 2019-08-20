from django.http import JsonResponse
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from organisations.libraries.get_organisation import get_organisation_by_pk
from users.libraries.get_user import get_users_from_organisation
from users.serializers import ExporterUserViewSerializer


class UsersList(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        List all users from the specified organisation
        """
        print('get into endpoint')
        organisation = get_organisation_by_pk(pk)

        view_serializer = ExporterUserViewSerializer(get_users_from_organisation(organisation), many=True)
        return JsonResponse(data={'users': view_serializer.data})
