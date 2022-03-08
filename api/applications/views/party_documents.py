from django.db import transaction
from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.applications.libraries.get_applications import get_application
from api.applications.libraries.document_helpers import upload_party_document, delete_party_document, get_party_document
from api.core.authentication import ExporterAuthentication
from api.core.decorators import authorised_to_view_application
from api.parties.models import PartyDocument
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

    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    def post(self, request, pk, party_pk):
        application = get_application(pk)
        party = application.get_party(party_pk)
        return upload_party_document(party, request.data, application, request.user)

    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    def delete(self, request, pk, party_pk):
        application = get_application(pk)
        party = application.get_party(party_pk)
        return delete_party_document(party, application, request.user)

    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    def delete(self, request, pk, party_pk, document_pk):
        application = get_application(pk)
        party = application.get_party(party_pk)
        if not party:
            return JsonResponse(data={"error": "No such user"}, status=status.HTTP_404_NOT_FOUND)

        try:
            document = PartyDocument.objects.get(id=document_pk)
            document.delete_s3()
            document.delete()

            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.DELETE_PARTY_DOCUMENT,
                target=application.get_case(),
                payload={"party_type": party.type.replace("_", " "), "party_name": party.name, "file_name": document.name},
            )

            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
        except PartyDocument.DoesNotExist:
            return JsonResponse(data={"error": "Party document does not exist"}, status=status.HTTP_404_NOT_FOUND)


        return delete_party_document(party, application, request.user)
