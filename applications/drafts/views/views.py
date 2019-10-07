from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.libraries.application_helpers import get_serializer_for_application
from applications.libraries.get_applications import get_application
from conf.authentication import ExporterAuthentication
from organisations.libraries.get_organisation import get_organisation_by_user


class DraftDetail(APIView):
    """
    Retrieve or delete a draft instance
    """
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        draft = get_application(pk=pk, organisation=organisation, submitted=False)

        serializer = get_serializer_for_application(draft)

        return JsonResponse(data={'application': serializer.data})

    def delete(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        draft = get_application(pk=pk, organisation=organisation, submitted=False)
        draft.delete()
        return JsonResponse(data={'status': 'Draft application deleted'},
                            status=status.HTTP_200_OK)
