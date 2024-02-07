from rest_framework import viewsets
from rest_framework.generics import RetrieveAPIView

from django.http import JsonResponse

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.core.authentication import SharedAuthentication
from api.documents.libraries.s3_operations import document_download_stream
from api.organisations import (
    filters,
    models,
    permissions,
    serializers,
)


class DocumentOnOrganisationView(viewsets.ModelViewSet):
    authentication_classes = (SharedAuthentication,)
    filter_backends = (filters.OrganisationFilter,)
    lookup_url_kwarg = "document_on_application_pk"
    permission_classes = (permissions.IsCaseworkerOrInDocumentOrganisation,)
    queryset = models.DocumentOnOrganisation.objects.all()
    serializer_class = serializers.DocumentOnOrganisationSerializer

    def list(self, request, pk):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(queryset, many=True)
        return JsonResponse({"documents": serializer.data})

    def retrieve(self, request, pk, document_on_application_pk):
        instance = self.get_object()
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
        instance = self.get_object()
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

    def update(self, request, pk, document_on_application_pk):
        instance = self.get_object()
        organisation = models.Organisation.objects.get(pk=pk)
        serializer = self.serializer_class(
            instance=instance, data=request.data, partial=True, context={"organisation": organisation}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.DOCUMENT_ON_ORGANISATION_UPDATE,
            target=organisation,
            payload={
                "file_name": instance.document.name,
                "document_type": instance.document_type,
            },
        )
        return JsonResponse({"document": serializer.data}, status=200)


class DocumentOnOrganisationStreamView(RetrieveAPIView):
    authentication_classes = (SharedAuthentication,)
    filter_backends = (filters.OrganisationFilter,)
    lookup_url_kwarg = "document_on_application_pk"
    permission_classes = (permissions.IsCaseworkerOrInDocumentOrganisation,)
    queryset = models.DocumentOnOrganisation.objects.filter(document__safe=True)

    def retrieve(self, request, *args, **kwargs):
        document = self.get_object()
        document = document.document
        return document_download_stream(document)
