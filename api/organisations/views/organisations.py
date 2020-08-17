from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics
from rest_framework.views import APIView
from api.applications.models import BaseApplication
from api.audit_trail.enums import AuditType
from api.core.authentication import (
    SharedAuthentication,
    OrganisationAuthentication,
    GovAuthentication,
)
from api.core.constants import GovPermissions
from api.core.helpers import str_to_bool
from api.core.permissions import check_user_has_permission, assert_user_has_permission
from lite_content.lite_api.strings import Organisations
from api.organisations.enums import OrganisationStatus, OrganisationType
from api.organisations.helpers import audit_edited_organisation_fields, audit_reviewed_organisation
from api.organisations.libraries.get_organisation import get_organisation_by_pk, get_request_user_organisation
from api.organisations.models import Organisation
from api.organisations.serializers import (
    OrganisationDetailSerializer,
    OrganisationCreateUpdateSerializer,
    OrganisationListSerializer,
    OrganisationStatusUpdateSerializer,
)
from api.audit_trail import service as audit_trail_service
from api.static.statuses.enums import CaseStatusEnum
from api.static.statuses.libraries.get_case_status import get_case_status_by_status
from api.static.statuses.models import CaseStatus
from api.users.enums import UserType
from api.workflow.flagging_rules_automation import apply_flagging_rules_to_case


class OrganisationsList(generics.ListCreateAPIView):
    authentication_classes = (OrganisationAuthentication,)
    serializer_class = OrganisationListSerializer

    def get_queryset(self):
        """ List all organisations. """
        if (
            getattr(self.request.user, "type", None) != UserType.INTERNAL
            and get_request_user_organisation(self.request).type != OrganisationType.HMRC
        ):
            raise PermissionError("Exporters aren't allowed to view other organisations")

        organisations = Organisation.objects.all()
        org_types = self.request.query_params.getlist("org_type", [])
        search_term = self.request.query_params.get("search_term")
        status = self.request.query_params.get("status")

        if org_types:
            organisations = organisations.filter(type__in=org_types)

        if search_term:
            organisations = organisations.filter(
                Q(name__icontains=search_term) | Q(registration_number__icontains=search_term)
            )

        if status:
            organisations = organisations.filter(status=status)

        return organisations

    @transaction.atomic
    @swagger_auto_schema(request_body=OrganisationCreateUpdateSerializer, responses={400: "JSON parse error"})
    def post(self, request):
        """ Create a new organisation. """
        data = request.data.copy()
        validate_only = request.data.get("validate_only", False)

        data["status"] = (
            OrganisationStatus.ACTIVE
            if getattr(request.user, "type", None) == UserType.INTERNAL
            else OrganisationStatus.IN_REVIEW
        )
        serializer = OrganisationCreateUpdateSerializer(data=data, context={"validate_only": validate_only})

        if serializer.is_valid(raise_exception=True):
            if not validate_only:
                serializer.save()

            # Audit the creation of the organisation
            if not request.user.is_anonymous:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.CREATED_ORGANISATION,
                    target=get_organisation_by_pk(serializer.data.get("id")),
                    payload={"organisation_name": serializer.data.get("name")},
                )
            else:
                audit_trail_service.create_system_user_audit(
                    verb=AuditType.REGISTER_ORGANISATION,
                    target=get_organisation_by_pk(serializer.data.get("id")),
                    payload={"email": request.data["user"]["email"], "organisation_name": serializer.data.get("name")},
                )

            return JsonResponse(data=serializer.data, status=status.HTTP_201_CREATED)


class OrganisationsDetail(generics.RetrieveUpdateAPIView):
    authentication_classes = (SharedAuthentication,)
    queryset = Organisation.objects.all()
    serializer_class = OrganisationDetailSerializer

    def put(self, request, pk):
        """ Edit details of an organisation. """
        organisation = get_organisation_by_pk(pk)
        org_name_changed = False

        if not check_user_has_permission(request.user, GovPermissions.MANAGE_ORGANISATIONS):
            return JsonResponse(data={"errors": Organisations.NO_PERM_TO_EDIT}, status=status.HTTP_400_BAD_REQUEST,)

        if request.data.get("name", organisation.name) != organisation.name:
            org_name_changed = True
            if not check_user_has_permission(request.user, GovPermissions.REOPEN_CLOSED_CASES):
                return JsonResponse(
                    data={"errors": Organisations.NO_PERM_TO_EDIT_NAME}, status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = OrganisationCreateUpdateSerializer(instance=organisation, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            if str_to_bool(request.data.get("validate_only", False)):
                return JsonResponse(data={"organisation": serializer.data}, status=status.HTTP_200_OK)

            is_non_uk = False if organisation.primary_site.address.address_line_1 else True
            audit_edited_organisation_fields(request.user, organisation, request.data, is_non_uk=is_non_uk)

            serializer.save()

            if org_name_changed:
                self.reopen_closed_cases_for_organisation(organisation)

            return JsonResponse(data={"organisation": serializer.data}, status=status.HTTP_200_OK)

    @staticmethod
    def reopen_closed_cases_for_organisation(organisation):
        """
        Set the case status to 'Reopened due to org changes' for any cases in the organisation that have
        been granted a licence.
        """
        reopened_due_to_org_changes_status = CaseStatus.objects.get(status="reopened_due_to_org_changes")

        applications = BaseApplication.objects.filter(
            organisation=organisation, status=get_case_status_by_status(CaseStatusEnum.FINALISED)
        )
        applications.update(status_id=reopened_due_to_org_changes_status)

        for application in applications:
            apply_flagging_rules_to_case(application)


class OrganisationsMatchingDetail(APIView):
    authentication_classes = (SharedAuthentication,)

    @staticmethod
    def _property_has_multiple_occurrences(queryset, property, property_name):
        return property and property in queryset.values_list(property_name, flat=True)

    def get(self, request, pk):
        matching_properties = []
        organisation = get_organisation_by_pk(pk)
        organisations_with_matching_details = Organisation.objects.filter(
            Q(name__isnull=False, name=organisation.name)
            | Q(eori_number__isnull=False, eori_number=organisation.eori_number)
            | Q(registration_number__isnull=False, registration_number=organisation.registration_number)
            | Q(
                primary_site__address__address_line_1__isnull=False,
                primary_site__address__address_line_1=organisation.primary_site.address.address_line_1,
            )
            | Q(
                primary_site__address__address__isnull=False,
                primary_site__address__address=organisation.primary_site.address.address,
            )
        ).exclude(id=pk)

        if organisations_with_matching_details.exists():
            if self._property_has_multiple_occurrences(organisations_with_matching_details, organisation.name, "name"):
                matching_properties.append(Organisations.MatchingProperties.NAME)

            if self._property_has_multiple_occurrences(
                organisations_with_matching_details, organisation.eori_number, "eori_number"
            ):
                matching_properties.append(Organisations.MatchingProperties.EORI)

            if self._property_has_multiple_occurrences(
                organisations_with_matching_details, organisation.registration_number, "registration_number"
            ):
                matching_properties.append(Organisations.MatchingProperties.REGISTRATION)

            if self._property_has_multiple_occurrences(
                organisations_with_matching_details,
                organisation.primary_site.address.address_line_1,
                "primary_site__address__address_line_1",
            ) or self._property_has_multiple_occurrences(
                organisations_with_matching_details,
                organisation.primary_site.address.address,
                "primary_site__address__address",
            ):
                matching_properties.append(Organisations.MatchingProperties.ADDRESS)

        return JsonResponse({"matching_properties": matching_properties})


class OrganisationStatusView(generics.UpdateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = OrganisationStatusUpdateSerializer

    def get_object(self):
        assert_user_has_permission(self.request.user, GovPermissions.MANAGE_ORGANISATIONS)
        return get_organisation_by_pk(self.kwargs["pk"])

    def update(self, request, *args, **kwargs):
        organisation = self.get_object()
        serializer = self.get_serializer(organisation, data=request.data)

        if serializer.is_valid():
            serializer.save()
            audit_reviewed_organisation(request.user, organisation, serializer.data["status"]["key"])

            return JsonResponse(data=serializer.data, status=status.HTTP_200_OK)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
