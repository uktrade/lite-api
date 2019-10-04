from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from applications.libraries.document_helpers import upload_draft_document, delete_draft_document, get_draft_document
from applications.serializers import ApplicationDocumentSerializer
from applications.libraries.document_helpers import get_draft_documents


class DraftDocumentView(APIView):
    """
    Retrieve or add document to a draft
    """

    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk):
        """
        View all additional documents on a draft.
        """
        return get_draft_documents(pk)

    @swagger_auto_schema(
        request_body=ApplicationDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def post(self, request, pk):
        """
        Upload additional document onto a draft.
        """
        return upload_draft_document(pk, request.data)


class DraftDocumentDetailView(APIView):
    """
    Retrieve or delete a document from a draft
    """

    authentication_classes = (ExporterAuthentication,)

    def get(self, request, pk, doc_pk):
        """
        View an additional document on a draft.
        """
        return get_draft_document(pk, doc_pk)

    @swagger_auto_schema(
        request_body=ApplicationDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic()
    def delete(self, request, pk, doc_pk):
        """
        Delete an additional document on a draft.
        """
        return delete_draft_document(doc_pk)
