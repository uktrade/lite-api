from django.db import transaction
from django.http import JsonResponse, Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from drafts.libraries.get_draft import get_draft
from end_user.end_user_document.models import DraftEndUserDocument
from end_user.serializers import DraftEndUserDocumentSerializer
from organisations.libraries.get_organisation import get_organisation_by_user


class EndUserDocuments(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns a list of documents on the specified end user
        """
        draft = get_draft(pk)
        end_user = draft.end_user
        draft_end_user_documents = DraftEndUserDocument.objects.filter(draft__id=draft.id, draft__end_user=end_user).order_by('-created_at')
        serializer = DraftEndUserDocumentSerializer(draft_end_user_documents, many=True)

        return JsonResponse({'documents': serializer.data})


    @swagger_auto_schema(
        request_body=DraftEndUserDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def post(self, request, pk):
        """
        Adds a document to the specified end user
        """

        draft = get_draft(pk)
        end_user = draft.end_user
        end_user_id = str(end_user.id)
        organisation = get_organisation_by_user(request.user)
        data = request.data

        if end_user.organisation != organisation:
            raise Http404

        for document in data:
            document['end_user'] = end_user_id
            document['user'] = request.user.id
            document['organisation'] = organisation.id

        serializer = DraftEndUserDocumentSerializer(data=data, many=True)

        if serializer.is_valid():
            print('SERIALIZER VALID')
            serializer.save()
            return JsonResponse({'documents': serializer.data}, status=status.HTTP_201_CREATED)

        print('SERIALIZER NOT VALID')
        return JsonResponse({'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

