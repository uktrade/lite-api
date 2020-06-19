from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from cases.enums import CaseTypeEnum
from cases.libraries.get_case import get_case
from cases.models import Case
from compliance.serializers import ComplianceLicenceListSerializer
from conf.authentication import GovAuthentication, SharedAuthentication, ExporterAuthentication
from lite_content.lite_api import strings
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from workflow.automation import run_routing_rules
from workflow.flagging_rules_automation import apply_flagging_rules_to_case

from compliance.helpers import (
    get_record_holding_sites_for_case,
    COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES,
)

from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView

from compliance.helpers import read_and_validate_csv, fetch_and_validate_licences
from compliance.models import OpenLicenceReturns
from compliance.serializers import (
    OpenLicenceReturnsCreateSerializer,
    OpenLicenceReturnsListSerializer,
    OpenLicenceReturnsViewSerializer,
)
from lite_content.lite_api.strings import Compliance
from organisations.libraries.get_organisation import get_request_user_organisation_id


class LicenceList(ListAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = ComplianceLicenceListSerializer

    def get_queryset(self):
        # For Compliance cases, when viewing from the site, we care about the Case the licence is attached to primarily,
        #   and the licence status (not added), and returns completed (not added).
        reference_code = self.request.GET.get("reference").upper()

        cases = Case.objects.select_related("case_type").filter(
            baseapplication__licence__is_complete=True,
            baseapplication__application_sites__site__site_records_located_at__compliance__id=self.kwargs["pk"],
        )
        cases = cases.filter(case_type__id__in=[CaseTypeEnum.OICL.id, CaseTypeEnum.OIEL.id]) | cases.filter(
            baseapplication__goods__good__control_list_entries__rating__regex=COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES,
            baseapplication__goods__licenced_quantity__isnull=False,
        )

        if reference_code:
            cases = cases.filter(reference_code__contains=reference_code)

        return cases


class ComplianceManageStatus(APIView):
    """
    Modify the status of a Compliance case
    """

    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):  # TODO: Move to CaseStatus endpoint
        case = get_case(pk)
        new_status = request.data.get("status")

        if new_status not in [CaseStatusEnum.OPEN, CaseStatusEnum.CLOSED]:
            return JsonResponse(data={"errors": [strings.Statuses.BAD_STATUS]}, status=status.HTTP_400_BAD_REQUEST,)

        old_status = case.status

        case.status = get_case_status_by_status(new_status)
        case.save()

        if CaseStatusEnum.is_terminal(old_status.status) and not CaseStatusEnum.is_terminal(case.status.status):
            apply_flagging_rules_to_case(case)

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.UPDATED_STATUS,
            target=case.get_case(),
            payload={"status": {"new": CaseStatusEnum.get_text(new_status), "old": old_status.status}},
        )

        # Case routing rules
        if old_status.status != new_status:
            run_routing_rules(case=case, keep_status=True)

        return JsonResponse(data={}, status=status.HTTP_200_OK)


class ComplianceCaseId(APIView):
    """
    This endpoint is currently only used for testing purposes. It gives us back the compliance case ids for the given case.
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request, pk, *args, **kwargs):
        # Get record holding sites for the case
        record_holding_sites_id = get_record_holding_sites_for_case(pk)

        # Get list of record holding sites that do not have a compliance case
        existing_compliance_cases = Case.objects.filter(
            compliancesitecase__site_id__in=record_holding_sites_id
        ).distinct()

        return JsonResponse(
            data={"ids": list(existing_compliance_cases.values_list("id", flat=True))}, status=status.HTTP_200_OK
        )


class OpenLicenceReturnsView(ListAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = OpenLicenceReturnsListSerializer

    def get_queryset(self):
        organisation_id = get_request_user_organisation_id(self.request)
        return OpenLicenceReturns.objects.filter(organisation_id=organisation_id).order_by("-year", "-created_at")

    def post(self, request):
        file = request.data.get("file")
        if not file:
            raise ValidationError({"file": [Compliance.OpenLicenceReturns.FILE_ERROR]})

        organisation_id = get_request_user_organisation_id(request)
        references, cleaned_text = read_and_validate_csv(file)
        licence_ids = fetch_and_validate_licences(references, organisation_id)

        data = request.data
        data["returns_data"] = cleaned_text
        data["licences"] = licence_ids
        data["organisation"] = organisation_id
        serializer = OpenLicenceReturnsCreateSerializer(data=data)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return JsonResponse(data={"open_licence_returns": serializer.data["id"]}, status=status.HTTP_201_CREATED)


class OpenLicenceReturnDownloadView(RetrieveAPIView):
    authentication_classes = (SharedAuthentication,)
    queryset = OpenLicenceReturns.objects.all()
    serializer_class = OpenLicenceReturnsViewSerializer
