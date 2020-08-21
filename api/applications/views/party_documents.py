from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from api.applications.libraries.get_applications import get_application
from api.applications.libraries.document_helpers import upload_party_document, delete_party_document, get_party_document
from api.core.authentication import ExporterAuthentication
from api.core.decorators import authorised_to_view_application
from api.parties.serializers import PartyDocumentSerializer
from api.users.models import ExporterUser


class PartyDocumentView(APIView):
    """
    Retrieve, add or delete an end user document from an application
    """

    authentication_classes = (ExporterAuthentication,)

    @authorised_to_view_application(ExporterUser)
    def get(self, request, pk, party_pk):
        application = get_application(pk)
        party = application.get_party(party_pk)
        return get_party_document(party)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    def post(self, request, pk, party_pk):
        application = get_application(pk)
        party = application.get_party(party_pk)
        return upload_party_document(party, request.data, application, request.user)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    def delete(self, request, pk, party_pk):
        application = get_application(pk)
        party = application.get_party(party_pk)
        return delete_party_document(party, application, request.user)
