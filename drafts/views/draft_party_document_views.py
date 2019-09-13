from django.db import transaction
from django.http import JsonResponse, HttpResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from drafts.libraries.get_document import get_document
from parties.document.models import PartyDocument
from parties.document.serializers import PartyDocumentSerializer
from drafts.libraries.get_party import get_end_user, get_ultimate_end_user, get_consignee, get_third_party


def _get_party_document(party):
    if not party:
        return JsonResponse(data={'error': 'No such user'},
                            status=status.HTTP_400_BAD_REQUEST)

    documents = PartyDocument.objects.filter(party=party)
    return get_document(documents)


def _upload_party_document(party, data):
    if not party:
        return JsonResponse(data={'error': 'No such user'},
                            status=status.HTTP_400_BAD_REQUEST)

    documents = PartyDocument.objects.filter(party=party)
    if documents:
        return JsonResponse(data={'error': 'Document already exists'},
                            status=status.HTTP_400_BAD_REQUEST)

    data['party'] = party.id
    serializer = PartyDocumentSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return JsonResponse({'document': serializer.data}, status=status.HTTP_201_CREATED)
    else:
        return JsonResponse({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


def _delete_party_document(party):
    if not party:
        return JsonResponse(data={'error': 'No such user'}, status=status.HTTP_400_BAD_REQUEST)

    documents = PartyDocument.objects.filter(party=party)
    for document in documents:
        document.delete_s3()
        document.delete()

    return HttpResponse(status=204)


class EndUserDocumentView(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns document for the specified end user
        """
        end_user = get_end_user(pk)
        return _get_party_document(end_user)

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
        return _upload_party_document(end_user, request.data)

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
        return _delete_party_document(end_user)


class UltimateEndUserDocumentsView(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk, ueu_pk):
        """
        Returns document for the specified ultimate end user
        """
        ultimate_end_user = get_ultimate_end_user(ueu_pk)
        return get_document(ultimate_end_user)

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
        return _upload_party_document(ultimate_end_user, request.data)

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
        return _delete_party_document(ultimate_end_user)


class ConsigneeDocumentView(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns document for the specified consignee
        """
        consignee = get_consignee(pk)
        return get_document(consignee)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def post(self, request, pk):
        """
        Adds a document to the specified consignee
        """
        consignee = get_consignee(pk)
        return _upload_party_document(consignee, request.data)

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
        consignee = get_consignee(pk)
        return _delete_party_document(consignee)


class ThirdPartyDocumentView(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns document for the specified third party
        """
        third_party = get_third_party(pk)
        return get_document(third_party)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def post(self, request, pk):
        """
        Adds a document to the specified consignee
        """
        third_party = get_third_party(pk)
        return _upload_party_document(third_party, request.data)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def delete(self, request, pk):
        """
        Deletes a document from the specified consignee
        """
        third_party = get_third_party(pk)
        return _delete_party_document(third_party)
