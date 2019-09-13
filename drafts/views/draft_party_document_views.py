from django.db import transaction
from django.http import JsonResponse, HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from drafts.libraries.get_document import get_document
from parties.document.models import PartyDocument
from parties.document.serializers import PartyDocumentSerializer
from drafts.libraries.get_party import get_end_user, get_ultimate_end_user


def _return_post_response(serializer):
    if serializer.is_valid():
        serializer.save()
        return JsonResponse({'document': serializer.data}, status=status.HTTP_201_CREATED)
    else:
        return JsonResponse({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EndUserDocumentView(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns document for the specified end user
        """
        end_user = get_end_user(pk)
        if not end_user:
            return JsonResponse(data={'error': 'No such user'},
                                status=status.HTTP_400_BAD_REQUEST)

        documents = PartyDocument.objects.filter(party=end_user)

        return get_document(documents)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def post(self, request, pk):
        """
        Adds a document to the specified end user
        """
        end_user = get_end_user(pk)
        if not end_user:
            return JsonResponse(data={'error': 'No such user'},
                                status=status.HTTP_400_BAD_REQUEST)

        end_user_documents = PartyDocument.objects.filter(party=end_user)
        if end_user_documents:
            return JsonResponse(data={'error': 'Document already exists'},
                                status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        data['party'] = end_user.id
        serializer = PartyDocumentSerializer(data=data)

        return _return_post_response(serializer)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def delete(self, request, pk):
        """
        Deletes a document from the specified end user
        """
        end_user = get_end_user(pk)
        if not end_user:
            return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_400_BAD_REQUEST)

        documents = PartyDocument.objects.filter(party=end_user)
        for document in documents:
            document.delete_s3()
            document.delete()

        return HttpResponse(status=204)


class UltimateEndUserDocumentsView(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk, ueu_pk):
        """
        Returns document for the specified ultimate end user
        """
        ultimate_end_user = get_ultimate_end_user(ueu_pk)
        if not ultimate_end_user:
            return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_400_BAD_REQUEST)

        documents = PartyDocument.objects.filter(party=ultimate_end_user)

        return get_document(documents)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def post(self, request, pk, ueu_pk):
        """
        Adds a document to the specified ultimate end user
        """
        ultimate_end_user = get_ultimate_end_user(ueu_pk)
        if not ultimate_end_user:
            return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_400_BAD_REQUEST)

        documents = PartyDocument.objects.filter(party=ultimate_end_user)
        if documents:
            return JsonResponse(data={'error': 'Document already exists'},
                                status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        data['party'] = ultimate_end_user.id
        serializer = PartyDocumentSerializer(data=data)

        return _return_post_response(serializer)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def delete(self, request, pk, ueu_pk):
        """
        Deletes a document from the specified ultimate end user
        """
        ultimate_end_user = get_ultimate_end_user(ueu_pk)
        if not ultimate_end_user:
            return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_400_BAD_REQUEST)

        documents = PartyDocument.objects.filter(party=ultimate_end_user)
        for document in documents:
            document.delete_s3()
            document.delete()

        return HttpResponse(status=204)
