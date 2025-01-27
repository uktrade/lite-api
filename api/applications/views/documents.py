from django.db import transaction
from django.http import JsonResponse
from rest_framework.views import APIView

from api.applications.libraries import document_helpers
from api.applications.libraries.get_applications import get_application
from api.applications.models import ApplicationDocument
from api.applications.serializers.document import ApplicationDocumentSerializer
from api.core.authentication import ExporterAuthentication
from api.core.decorators import (
    authorised_to_view_application,
    application_is_editable,
)
from api.users.models import ExporterUser


class ApplicationDocumentView(APIView):
    """
    Retrieve or add document to an application
    """

    authentication_classes = (ExporterAuthentication,)

    @authorised_to_view_application(ExporterUser)
    def get(self, request, pk):
        """
        View all additional documents on an application
        """

        application = get_application(pk)

        documents = ApplicationDocumentSerializer(ApplicationDocument.objects.filter(application_id=pk), many=True).data

        return JsonResponse({"documents": documents, "editable": application.is_major_editable()})

    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    @application_is_editable
    def post(self, request, pk):
        """
        Upload additional document onto an application
        """

        application = get_application(pk)

        return document_helpers.upload_application_document(application, request.data, request.user)


class ApplicationDocumentDetailView(APIView):
    """
    Retrieve or delete a document from an application
    """

    authentication_classes = (ExporterAuthentication,)

    @authorised_to_view_application(ExporterUser)
    def get(self, request, pk, doc_pk):
        """
        View an additional document on an application
        """
        return document_helpers.get_application_document(doc_pk)

    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    @application_is_editable
    def delete(self, request, pk, doc_pk):
        """
        Delete an additional document on an application
        """
        application = get_application(pk)
        return document_helpers.delete_application_document(doc_pk, application, request.user)
