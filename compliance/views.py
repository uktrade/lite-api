from django.db.models import When, Case as db_case, F
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

from applications.libraries.application_helpers import can_status_be_set_by_gov_user
from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from cases.libraries.get_case import get_case
from cases.models import Case
from compliance.serializers import ComplianceLicenceListSerializer
from conf.authentication import GovAuthentication
from organisations.models import Site
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from workflow.automation import run_routing_rules
from workflow.flagging_rules_automation import apply_flagging_rules_to_case


class LicenceList(ListAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = ComplianceLicenceListSerializer

    def get_queryset(self):
        # For Compliance cases, when viewing from the site, we care about the Case the licence is attached to primarily,
        #   and the licence status (not added), and returns completed (not added).
        return Case.objects.filter(
            baseapplication__licence__is_complete=True,
            baseapplication__application_sites__site__compliance__id=self.kwargs["pk"],
        ) | Case.objects.filter(
            baseapplication__licence__is_complete=True,
            baseapplication__application_sites__site__site_records_located_at__compliance__id=self.kwargs["pk"],
        )


class ComplianceManageStatus(APIView):
    """
    Modify the status of a Compliance case
    """

    authentication_classes = (GovAuthentication,)

    def put(self, request, pk):
        case = get_case(pk)
        new_status = request.data.get("status")

        if not can_status_be_set_by_gov_user(
                request.user, case.status.status, new_status, is_licence_application=False
        ):
            return JsonResponse(
                data={"errors": ["Status cannot be set by Gov user."]}, status=status.HTTP_400_BAD_REQUEST
            )

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
        # Get record holding sites the case
        record_holding_sites_id = list(
            Site.objects.filter(sites_on_application__application_id=pk)
                .annotate(
                record_site=db_case(
                    When(site_records_located_at__isnull=False, then=F("site_records_located_at")), default=F("id")
                )
            )
                .values_list("record_site", flat=True)
        )

        # Get list of record holding sites that do not relate to compliance case

        existing_compliance_cases = Case.objects.filter(
            compliancesitecase__site_id__in=record_holding_sites_id).distinct()

        return JsonResponse(data={"ids": list(existing_compliance_cases.values_list("id", flat=True))},
                            status=status.HTTP_200_OK)
