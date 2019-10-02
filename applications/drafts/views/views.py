from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from applications.enums import ApplicationLicenceType
from applications.libraries.application_helpers import get_serializer_for_application
from applications.libraries.get_applications import get_draft_with_organisation, get_drafts_with_organisation
from applications.models import StandardApplication, OpenApplication
from applications.serializers import BaseApplicationSerializer, ApplicationCreateSerializer
from conf.authentication import ExporterAuthentication
from organisations.libraries.get_organisation import get_organisation_by_user


class DraftList(APIView):
    authentication_classes = (ExporterAuthentication,)
    """
    List all drafts that belong to an organisation and create a new draft.
    """

    def get(self, request):
        organisation = get_organisation_by_user(request.user)

        drafts = get_drafts_with_organisation(organisation)

        serializer = BaseApplicationSerializer(drafts, many=True)
        return JsonResponse(data={'drafts': serializer.data})

    def post(self, request):
        organisation = get_organisation_by_user(request.user)
        data = request.data
        data['organisation'] = str(organisation.id)

        # Use generic serializer to validate all types of application as we may not yet know the application type
        serializer = ApplicationCreateSerializer(data=data)

        if serializer.is_valid():
            serializer.validated_data['organisation'] = organisation

            # Use the data from the generic serializer to determine which model to save to
            if serializer.validated_data['licence_type'] == ApplicationLicenceType.STANDARD_LICENCE:
                application = StandardApplication(**serializer.validated_data)
            else:
                application = OpenApplication(**serializer.validated_data)

            application.save()

            return JsonResponse(data={'draft': {**serializer.data, 'id': str(application.id)}},
                                status=status.HTTP_201_CREATED)

        return JsonResponse(data={'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class DraftDetail(APIView):
    authentication_classes = (ExporterAuthentication,)
    """
    Retrieve, update or delete a draft instance.
    """

    def get(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        draft = get_draft_with_organisation(pk=pk, organisation=organisation)

        serializer = get_serializer_for_application(draft)

        return JsonResponse(data={'draft': serializer.data})

    def delete(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        draft = get_draft_with_organisation(pk, organisation)
        draft.delete()
        return JsonResponse(data={'status': 'Draft Deleted'},
                            status=status.HTTP_200_OK)
