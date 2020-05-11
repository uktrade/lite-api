from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView

from applications.libraries.document_helpers import upload_party_document, delete_party_document, get_party_document
from conf.authentication import ExporterAuthentication
from conf.decorators import authorised_users
from parties.serializers import PartyDocumentSerializer
from users.models import ExporterUser


class PartyDocumentView(APIView):
    """
    Retrieve, add or delete an end user document from an application
    """

    authentication_classes = (ExporterAuthentication,)

    @authorised_users(ExporterUser)
    def get(self, request, application, party_pk):
        party = application.get_party(party_pk)
        return get_party_document(party)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @authorised_users(ExporterUser)
    def post(self, request, application, party_pk):
        party = application.get_party(party_pk)
        return upload_party_document(party, request.data, application, request.user)

    @swagger_auto_schema(request_body=PartyDocumentSerializer, responses={400: "JSON parse error"})
    @transaction.atomic
    @authorised_users(ExporterUser)
    def delete(self, request, application, party_pk):
        party = application.get_party(party_pk)
        return delete_party_document(party, application, request.user)
