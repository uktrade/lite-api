from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from drafts.libraries.document_helpers import upload_draft_document, delete_draft_document, get_draft_document
from drafts.serializers import DraftDocumentsSerializer
from drafts.libraries.document_helpers import get_draft_documents


class DraftDocumentView(APIView):
    """
    Retrieve or add document from a draft
    """

    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        return get_draft_documents(pk)

    @swagger_auto_schema(
        request_body=DraftDocumentsSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def post(self, request, pk):
        return upload_draft_document(pk, request.data)


class DraftDocumentDetailView(APIView):
    """
    Retrieve or delete a document from a draft
    """

    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk, doc_pk):
        return get_draft_document(pk, doc_pk)

    @swagger_auto_schema(
        request_body=DraftDocumentsSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def delete(self, request, pk, doc_pk):
        return delete_draft_document(doc_pk)
