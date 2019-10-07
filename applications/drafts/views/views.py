from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.libraries.application_helpers import get_serializer_for_application
from applications.libraries.get_applications import get_draft_application_for_organisation
from conf.authentication import ExporterAuthentication
from organisations.libraries.get_organisation import get_organisation_by_user


class DraftDetail(APIView):
    """
    Retrieve or delete a draft instance
    """
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        draft = get_draft_application_for_organisation(pk=pk, organisation=organisation)

        serializer = get_serializer_for_application(draft)

        return JsonResponse(data={'draft': serializer.data})

    def delete(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        draft = get_draft_application_for_organisation(pk, organisation)
        draft.delete()
        return JsonResponse(data={'status': 'Draft Deleted'},
                            status=status.HTTP_200_OK)
