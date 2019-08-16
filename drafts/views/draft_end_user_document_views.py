from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseServerError
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from drafts.libraries.get_draft import get_draft
from end_user.end_user_document.models import EndUserDocument
from end_user.serializers import EndUserDocumentSerializer


class EndUserDocuments(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns a list of documents on the specified end user
        """
        draft = get_draft(pk)
        end_user = draft.end_user
        if end_user is None:
            return JsonResponse(data={'error': 'No such user'},
                                status=status.HTTP_400_BAD_REQUEST)
        end_user_documents = EndUserDocument.objects.filter(end_user=end_user)
        serializer = EndUserDocumentSerializer(end_user_documents, many=True)

        return JsonResponse({'documents': serializer.data})


    @swagger_auto_schema(
        request_body=EndUserDocumentSerializer,
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

        if end_user is None:
            return JsonResponse(data={'error': 'No such user'},
                                status=status.HTTP_400_BAD_REQUEST)

        end_user_id = str(end_user.id)
        data = request.data

        for document in data:
            document['end_user'] = end_user_id

        serializer = EndUserDocumentSerializer(data=data, many=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'documents': serializer.data}, status=status.HTTP_201_CREATED)

        return JsonResponse({'errors': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


    @swagger_auto_schema(
        request_body=EndUserDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def delete(self, request, pk):
        """
        Deletes a document from the specified end user
        """
        draft = get_draft(pk)
        end_user = draft.end_user

        if end_user is None:
            return JsonResponse(data={'error': 'No such user'},
                                status=status.HTTP_400_BAD_REQUEST)

        return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_500)

        # draft = get_draft(pk)
        # end_user = draft.end_user
        # doc  = EndUserDocument.objects.get(id=dr)
        # end_user_id = str(end_user.id)
        # organisation = get_organisation_by_user(request.user)
        # data = request.data
