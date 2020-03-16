import operator
from functools import reduce

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics

from applications.models import BaseApplication
from conf.authentication import SharedAuthentication, OrganisationAuthentication
from conf.constants import GovPermissions
from conf.helpers import str_to_bool
from conf.permissions import check_user_has_permission
from lite_content.lite_api.strings import Organisations
from organisations.enums import OrganisationStatus, OrganisationType
from organisations.libraries.get_organisation import get_organisation_by_pk
from organisations.models import Organisation
from organisations.serializers import (
    OrganisationDetailSerializer,
    OrganisationCreateSerializer,
    OrganisationListSerializer,
)
from static.statuses.models import CaseStatus
from users.enums import UserType


class OrganisationsList(generics.ListCreateAPIView):
    authentication_classes = (OrganisationAuthentication,)
    serializer_class = OrganisationListSerializer

    def get_queryset(self):
        """ List all organisations. """
        if (
            getattr(self.request.user, "type", None) != UserType.INTERNAL
            and self.request.user.organisation.type != OrganisationType.HMRC
        ):
            raise PermissionError("Exporters aren't allowed to view other organisations")

        org_types = self.request.query_params.getlist("org_type", [])
        search_term = self.request.query_params.get("search_term", "")

        query = [Q(name__icontains=search_term) | Q(registration_number__icontains=search_term)]

        result = Organisation.objects.filter(reduce(operator.and_, query))

        if org_types:
            result = result.filter(Q(type__in=org_types))

        return result

    @transaction.atomic
    @swagger_auto_schema(request_body=OrganisationCreateSerializer, responses={400: "JSON parse error"})
    def post(self, request):
        """ Create a new organisation. """
        data = request.data.copy()
        validate_only = request.data.get("validate_only", False)
        data["status"] = (
            OrganisationStatus.ACTIVE
            if getattr(request.user, "type", None) == UserType.INTERNAL
            else OrganisationStatus.IN_REVIEW
        )
        serializer = OrganisationCreateSerializer(data=data, context={"validate_only": validate_only})

        if serializer.is_valid():
            if not validate_only:
                serializer.save()
            return JsonResponse(data=serializer.data, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class OrganisationsDetail(generics.RetrieveAPIView):
    authentication_classes = (SharedAuthentication,)
    queryset = Organisation.objects.all()
    serializer_class = OrganisationDetailSerializer

    def put(self, request, pk):
        """ Edit details of an organisation. """
        organisation = get_organisation_by_pk(pk)
        org_name_changed = False

        if not check_user_has_permission(request.user, GovPermissions.MANAGE_ORGANISATIONS):
            return JsonResponse(data={"errors": Organisations.NO_PERM_TO_EDIT}, status=status.HTTP_400_BAD_REQUEST,)

        if request.data["name"] != organisation.name:
            org_name_changed = True
            if not check_user_has_permission(request.user, GovPermissions.REOPEN_CLOSED_CASES):
                return JsonResponse(
                    data={"errors": Organisations.NO_PERM_TO_EDIT_NAME}, status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = OrganisationCreateSerializer(instance=organisation, data=request.data, partial=True)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if str_to_bool(request.data.get("validate_only", False)):
            return JsonResponse(data={"organisation": serializer.data}, status=status.HTTP_200_OK)

        serializer.save()
        if org_name_changed:
            self.reopen_closed_cases_for_organisation(organisation)

        return JsonResponse(data={"organisation": serializer.validated_data}, status=status.HTTP_201_CREATED)

    @staticmethod
    def reopen_closed_cases_for_organisation(organisation):
        """
        Set the case status to 'Reopened due to org changes' for any cases in the organisation that have
        been granted a licence.
        """
        reopened_due_to_org_changes_status = CaseStatus.objects.get(status="reopened_due_to_org_changes")

        BaseApplication.objects.filter(organisation=organisation, licence_duration__isnull=False).update(
            status_id=reopened_due_to_org_changes_status
        )
