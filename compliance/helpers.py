import csv
import re
from typing import Optional

from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from audit_trail.enums import AuditType
from audit_trail.models import Audit
from cases.enums import CaseTypeEnum
from cases.models import Case
from compliance.models import ComplianceSiteCase, ComplianceVisitCase, CompliancePerson
from conf.constants import ExporterPermissions
from conf.exceptions import NotFoundError
from conf.permissions import check_user_has_permission
from goods.models import Good
from licences.models import Licence
from lite_content.lite_api import strings
from lite_content.lite_api.strings import Compliance
from organisations.libraries.get_organisation import get_request_user_organisation
from organisations.models import Site, Organisation
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.enums import SystemUser
from users.models import BaseUser


def get_compliance_site_case(pk):
    """
    Returns a compliance site case or returns a 404 on failure
    """
    try:
        return ComplianceSiteCase.objects.get(pk=pk)
    except ComplianceSiteCase.DoesNotExist:
        raise NotFoundError({"case": strings.Cases.CASE_NOT_FOUND})


# SIEL type compliance cases require a specific control code prefixes. currently: (0 to 9)D, (0 to 9)E, ML21, ML22.
COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES = "(^[0-9][DE].*$)|(^ML21.*$)|(^ML22.*$)"


def case_meets_conditions_for_compliance(case: Case):
    if case.case_type.id == CaseTypeEnum.SIEL.id:
        if not (
            Good.objects.filter(
                goods_on_application__application_id=case.id,
                control_list_entries__rating__regex=COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES,
                goods_on_application__licenced_quantity__isnull=False,
            ).exists()
        ):
            return False
        return True
    elif case.case_type.id in [CaseTypeEnum.OIEL.id, CaseTypeEnum.OICL.id, *CaseTypeEnum.OGL_ID_LIST]:
        return True
    else:
        return False


def get_record_holding_sites_for_case(case):
    if case.case_type.id in CaseTypeEnum.OGL_ID_LIST:
        return {case.site.site_records_located_at_id}
    else:
        return set(
            Site.objects.filter(sites_on_application__application_id=case.id).values_list(
                "site_records_located_at_id", flat=True
            )
        )


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
                actor=system_user, verb=AuditType.COMPLIANCE_SITE_CASE_CREATE, target=comp_case.get_case(), payload={},
            )
        )

    Audit.objects.bulk_create(audits)


TOTAL_COLUMNS = 5


def read_and_validate_csv(text):
    """
    Used for parsing Open Licence returns CSV files which are uploaded by the exporter for certain case types
    and contain the Licence reference as well as other properties for compliance.

    Takes CSV formatted text and returns the licence references & cleaned format of the CSV.
    Requires the first column to be the licence reference.
    Requires 5 items per row or throws a ValidationError.
    Requires the first line to be blank/headers or data will be lost.
    """
    references = set()
    cleaned_text = ""

    try:
        csv_reader = csv.reader(text.split("\n"), delimiter=",")
        # skip headers
        next(csv_reader, None)
        for row in csv_reader:
            if row:
                if len(row) != TOTAL_COLUMNS:
                    raise ValidationError({"file": [Compliance.OpenLicenceReturns.INVALID_FILE_FORMAT]})
                references.add(row[0])
                # https://owasp.org/www-community/attacks/CSV_Injection
                cleaned_text += ",".join([re.sub("[^A-Za-z0-9/,.-]+", "", item.strip()) for item in row]) + "\n"
    except csv.Error:
        raise ValidationError({"file": [Compliance.OpenLicenceReturns.INVALID_FILE_FORMAT]})

    return references, cleaned_text


def fetch_and_validate_licences(references, organisation_id):
    if len(references) == 0:
        raise ValidationError({"file": [Compliance.OpenLicenceReturns.INVALID_LICENCES]})

    licence_ids = list(
        Licence.objects.filter(reference_code__in=references, application__organisation_id=organisation_id).values_list(
            "id", flat=True
        )
    )
    if len(licence_ids) != len(references):
        raise ValidationError({"file": [Compliance.OpenLicenceReturns.INVALID_LICENCES]})

    return licence_ids


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
    if not check_user_has_permission(request.user, ExporterPermissions.ADMINISTER_SITES, organisation):
        sites = Site.objects.get_by_user_and_organisation(request.user, organisation).values_list("id", flat=True)
        qs = qs.filter(site__in=sites)

    return qs


def filter_cases_with_compliance_related_licence_attached(queryset, compliance_case_id):
    """
    Given a queryset of cases, and a compliance case id, determines cases which contain a licence connected
        to the site that compliance case is interested in, and that meet the conditions for a compliance case
    """
    queryset = queryset.filter(
        Q(
            baseapplication__licence__is_complete=True,
            baseapplication__application_sites__site__site_records_located_at__compliance__id=compliance_case_id,
        )
        | Q(opengenerallicencecase__site__site_records_located_at__compliance__id=compliance_case_id)
    )

    # We filter for OIEL, OICL and specific SIELs (dependant on CLC codes present) as these are the only case
    #   types relevant for compliance cases
    queryset = queryset.filter(
        case_type__id__in=[CaseTypeEnum.OICL.id, CaseTypeEnum.OIEL.id, *CaseTypeEnum.OGL_ID_LIST]
    ) | queryset.filter(
        baseapplication__goods__good__control_list_entries__rating__regex=COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES,
        baseapplication__goods__licenced_quantity__isnull=False,
    )

    return queryset
