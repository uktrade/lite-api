from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from drafts.libraries.document_helpers import upload_party_document, delete_party_document, get_party_document
from parties.document.serializers import PartyDocumentSerializer
from drafts.libraries.get_party import get_end_user, get_ultimate_end_user, get_consignee, get_third_party


class EndUserDocumentView(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns document for the specified end user
        """
        end_user = get_end_user(pk)
        return get_party_document(end_user)

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
        return upload_party_document(end_user, request.data)

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
        return delete_party_document(end_user)


class UltimateEndUserDocumentsView(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk, ueu_pk):
        """
        Returns document for the specified ultimate end user
        """
        ultimate_end_user = get_ultimate_end_user(ueu_pk)
        return get_party_document(ultimate_end_user)

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
        return upload_party_document(ultimate_end_user, request.data)

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
        return delete_party_document(ultimate_end_user)


class ConsigneeDocumentView(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        Returns document for the specified consignee
        """
        consignee = get_consignee(pk)
        return get_party_document(consignee)

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
        return upload_party_document(consignee, request.data)

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
        return delete_party_document(consignee)


class ThirdPartyDocumentView(APIView):
    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk, tp_pk):
        """
        Returns document for the specified third party
        """
        third_party = get_third_party(tp_pk)
        return get_party_document(third_party)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def post(self, request, pk, tp_pk):
        """
        Adds a document to the specified consignee
        """
        third_party = get_third_party(tp_pk)
        return upload_party_document(third_party, request.data)

    @swagger_auto_schema(
        request_body=PartyDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def delete(self, request, pk, tp_pk):
        """
        Deletes a document from the specified consignee
        """
        third_party = get_third_party(tp_pk)
        return delete_party_document(third_party)
