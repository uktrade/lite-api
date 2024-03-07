from django.db import transaction
from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.applications.libraries.get_applications import get_application
from api.applications.libraries.document_helpers import upload_party_document, delete_party_document, get_party_document
from api.applications.permissions import IsPartyDocumentInOrganisation
from api.core.authentication import ExporterAuthentication
from api.core.views import DocumentStreamAPIView
from api.core.decorators import authorised_to_view_application
from api.parties.models import PartyDocument
from api.users.models import ExporterUser


class PartyDocumentView(APIView):
    """
    Retrieve, add or delete an end user document from an application
    """

    authentication_classes = (ExporterAuthentication,)

    @property
    def application(self):
        return get_application(self.kwargs["pk"])

    @property
    def party(self):
        return self.application.get_party(self.kwargs["party_pk"])

    @authorised_to_view_application(ExporterUser)
    def get(self, request, **kwargs):
        return get_party_document(self.party)

    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    def post(self, request, **kwargs):
        return upload_party_document(self.party, request.data, self.application, request.user)

    @transaction.atomic
    @authorised_to_view_application(ExporterUser)
    def delete(self, request, **kwargs):
        document_pk = self.kwargs.get("document_pk")
        if not document_pk:
            return delete_party_document(self.party, self.application, request.user)

        try:
            document = PartyDocument.objects.get(id=document_pk)
        except PartyDocument.DoesNotExist:
            return JsonResponse(data={"error": "Party document does not exist"}, status=status.HTTP_404_NOT_FOUND)

        document.delete_s3()
        document.delete()

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.DELETE_PARTY_DOCUMENT,
            target=self.application.get_case(),
            payload={
                "party_type": self.party.type.replace("_", " "),
                "party_name": self.party.name,
                "file_name": document.name,
            },
        )

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)


class PartyDocumentStream(DocumentStreamAPIView):
    authentication_classes = (ExporterAuthentication,)
    lookup_url_kwarg = "document_pk"
    permission_classes = (IsPartyDocumentInOrganisation,)

    def get_queryset(self):
        return PartyDocument.objects.filter(
            party_id=self.kwargs["party_pk"],
            party__parties_on_application__application__id=self.kwargs["pk"],
        )

    def get_document(self, instance):
        return instance
