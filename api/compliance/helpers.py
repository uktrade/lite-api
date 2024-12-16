from typing import Optional

from django.utils import timezone
from django.conf import settings


from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.enums import CaseTypeEnum
from api.cases.models import Case
from api.compliance.enums import COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES
from api.compliance.models import ComplianceSiteCase, ComplianceVisitCase, CompliancePerson
from api.core.constants import ExporterPermissions
from api.core.exceptions import NotFoundError
from api.core.permissions import check_user_has_permission
from api.goods.models import Good
from lite_content.lite_api import strings
from api.organisations.libraries.get_organisation import get_request_user_organisation
from api.organisations.models import Site, Organisation
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.users.enums import SystemUser
from api.users.models import BaseUser


def get_compliance_site_case(pk):
    """
    Returns a compliance site case or returns a 404 on failure
    """
    try:
        return ComplianceSiteCase.objects.get(pk=pk)
    except ComplianceSiteCase.DoesNotExist:
        raise NotFoundError({"case": strings.Cases.CASE_NOT_FOUND})


def case_meets_conditions_for_compliance(case: Case):
    if case.case_type.id == CaseTypeEnum.SIEL.id:
        if settings.FEATURE_SIEL_COMPLIANCE_ENABLED:
            if Good.objects.filter(
                goods_on_application__application_id=case.id,
                control_list_entries__rating__regex=COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES,
                goods_on_application__licence__quantity__isnull=False,
            ).exists():
                return True
        return False
    else:
        return False


def get_record_holding_sites_for_case(case):
    return set(
        Site.objects.filter(sites_on_application__application_id=case.id).values_list(
            "site_records_located_at_id", flat=True
        )
    )  # pragma: no cover


def generate_compliance_site_case(case: Case):
    # check if case meets conditions required
    if not case_meets_conditions_for_compliance(case):
        return

    # Get record holding sites for the case
    record_holding_sites_id = get_record_holding_sites_for_case(case)

    # Get list of record holding sites that do not have a compliance case
    new_compliance_sites = Site.objects.filter(id__in=record_holding_sites_id, compliance__isnull=True).distinct()

    # Get a list compliance cases that already exist
    existing_compliance_cases = Case.objects.filter(compliancesitecase__site_id__in=record_holding_sites_id).distinct()

    audits = []
    system_user = BaseUser.objects.get(id=SystemUser.id)

    # Audit existing compliance cases to say new licence exists
    for comp_case in existing_compliance_cases:
        audits.append(
            Audit(
                actor=system_user,
                verb=AuditType.COMPLIANCE_SITE_CASE_NEW_LICENCE,
                target=comp_case,
                payload={"case_reference": case.reference_code},
            )
        )

    # Create new compliance cases for each record holding site without a case, and audit creation
    for site in new_compliance_sites:
        comp_case = ComplianceSiteCase(
            site=site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
            organisation_id=case.organisation_id,
            case_type_id=CaseTypeEnum.COMPLIANCE_SITE.id,
            submitted_at=timezone.now(),  # submitted_at is set since SLA falls over if not given
        )
        comp_case.save()
        audits.append(
            Audit(
                actor=system_user,
                verb=AuditType.COMPLIANCE_SITE_CASE_CREATE,
                target=comp_case.get_case(),
                payload={},
            )
        )

    Audit.objects.bulk_create(audits)


TOTAL_COLUMNS = 5


def compliance_visit_case_complete(case: ComplianceVisitCase) -> bool:
    """
    Function to ensure that all the details of a ComplianceVisitCase is filled in, allowing for the status to be changed
        to closed (terminal).
    :param case: ComplianceVisitCase to be looked at
    :return: boolean
    """
    fields = [
        "visit_type",
        "visit_date",
        "overall_risk_value",
        "licence_risk_value",
        "overview",
        "inspection",
        "compliance_overview",
        "compliance_risk_value",
        "individuals_overview",
        "individuals_risk_value",
        "products_overview",
        "products_risk_value",
    ]

    for field in fields:
        if not getattr(case, field):
            return False

    return CompliancePerson.objects.filter(visit_case_id=case.id).exists()


def get_exporter_visible_compliance_site_cases(request, organisation: Optional[Organisation]):
    if not organisation:
        organisation = get_request_user_organisation(request)
    qs = ComplianceSiteCase.objects.select_related("site", "site__address").filter(organisation_id=organisation.id)

    # if user does not have permission to manage all sites, filter by sites accessible
    if not check_user_has_permission(request.user.exporteruser, ExporterPermissions.ADMINISTER_SITES, organisation):
        sites = Site.objects.get_by_user_and_organisation(request.user.exporteruser, organisation).values_list(
            "id", flat=True
        )
        qs = qs.filter(site__in=sites)

    return qs
