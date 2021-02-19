from rest_framework import viewsets

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

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
        serializer.save()
        return JsonResponse({"document": serializer.data}, status=201)
