from rest_framework import viewsets

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.core.authentication import SharedAuthentication
from api.organisations import models, serializers


class DocumentOnOrganisationView(viewsets.ModelViewSet):
    authentication_classes = (SharedAuthentication,)
    serializer_class = serializers.DocumentOnOrganisationSerializer

    def get_queryset(self):
        return models.DocumentOnOrganisation.objects.filter(organisation_id=self.kwargs["pk"])

    def list(self, request, pk):
        serializer = self.serializer_class(self.get_queryset(), many=True)
        return JsonResponse({"documents": serializer.data})

    def retrieve(self, request, pk, document_on_application_pk):
        instance = get_object_or_404(self.get_queryset(), pk=document_on_application_pk)
        serializer = self.serializer_class(instance)
        return JsonResponse(serializer.data)

    def create(self, request, pk):
        organisation = models.Organisation.objects.get(pk=pk)
        serializer = self.serializer_class(data=request.data, context={"organisation": organisation})
        serializer.is_valid(raise_exception=True)
        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.DOCUMENT_ON_ORGANISATION_CREATE,
            target=organisation,
            payload={
                "file_name": request.data["document"]["name"],
                "document_type": request.data["document_type"],
            },
        )

        serializer.save()
        return JsonResponse({"document": serializer.data}, status=201)

    def delete(self, request, pk, document_on_application_pk):
        instance = get_object_or_404(self.get_queryset(), pk=document_on_application_pk)
        instance.delete()
        organisation = models.Organisation.objects.get(pk=pk)
        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.DOCUMENT_ON_ORGANISATION_DELETE,
            target=organisation,
            payload={
                "file_name": instance.document.name,
                "document_type": instance.document_type,
            },
        )
        return JsonResponse({}, status=204)
