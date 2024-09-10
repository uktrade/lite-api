from uuid import UUID
from django.http import JsonResponse
from api.core.authentication import GovAuthentication
from api.core.permissions import CanCaseworkersManageOrgainsation
from api.organisations.models import Organisation

from api.organisations.caseworker.serializers.serializers import ExporterUserCreateSerializer

from rest_framework import status
from rest_framework.generics import CreateAPIView


class CreateExporterUser(CreateAPIView):
    authentication_classes = (GovAuthentication,)

    serializer_class = ExporterUserCreateSerializer
    permission_classes = [CanCaseworkersManageOrgainsation]

    def post(self, request, org_pk):
        """
        Caseworker View to Create Exporter
        """

        data = request.data

        data["organisation"] = org_pk
        data["role"] = UUID(data["role"])
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            return JsonResponse(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        response_data = serializer.data
        orgainsation = Organisation.objects.get(id=org_pk)
        orgainsation.notify_exporter_user_added(serializer.validated_data["email"])
        orgainsation.add_case_note_add_export_user(request.user, data["sites"], serializer.validated_data["email"])

        return JsonResponse(data=response_data, status=status.HTTP_201_CREATED)
