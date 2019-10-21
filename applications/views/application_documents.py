from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from conf.authentication import ExporterAuthentication
from applications.libraries.document_helpers import upload_application_document, delete_application_document, \
    get_application_document
from applications.serializers import ApplicationDocumentSerializer
from applications.libraries.document_helpers import get_application_documents
from conf.decorators import authorised_users, application_licence_type, application_in_major_editable_state
from users.models import ExporterUser


class ApplicationDocumentView(APIView):
    """
    Retrieve or add document to an application
    """
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application):
        """
        View all additional documents on an application
        """
        return get_application_documents(application.id)

    @swagger_auto_schema(
        request_body=ApplicationDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def post(self, request, application):
        """
        Upload additional document onto an application
        """
        return upload_application_document(application.id, request.data)


class ApplicationDocumentDetailView(APIView):
    """
    Retrieve or delete a document from an application
    """
    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application, doc_pk):
        """
        View an additional document on an application
        """
        return get_application_document(application.id, doc_pk)

    @swagger_auto_schema(
        request_body=ApplicationDocumentSerializer,
        responses={
            400: 'JSON parse error'
        })
    @transaction.atomic
    @application_in_major_editable_state()
    @authorised_users(ExporterUser)
    def delete(self, request, application, doc_pk):
        """
        Delete an additional document on an application
        """
        return delete_application_document(doc_pk)
