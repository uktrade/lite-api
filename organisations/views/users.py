from django.http import JsonResponse
from rest_framework.views import APIView

from conf.authentication import SharedAuthentication
from organisations.libraries.get_organisation import get_organisation_by_pk
from users.libraries.get_user import get_users_from_organisation
from users.serializers import ExporterUserViewSerializer


class OrganisationUsersList(APIView):
    authentication_classes = (SharedAuthentication,)

    def get(self, request, org_pk):
        """
        List all users from the specified organisation
        """
        organisation = get_organisation_by_pk(org_pk)

        view_serializer = ExporterUserViewSerializer(get_users_from_organisation(organisation), many=True)
        return JsonResponse(data={'users': view_serializer.data})
