import csv
import re

from rest_framework.exceptions import ValidationError
from django.utils import timezone

from audit_trail.enums import AuditType
from audit_trail.models import Audit
from cases.enums import CaseTypeEnum
from cases.models import Case
from compliance.models import ComplianceSiteCase
from conf.exceptions import NotFoundError
from goods.models import Good
from lite_content.lite_api import strings
from organisations.models import Site
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.enums import SystemUser
from users.models import BaseUser
from licences.models import Licence
from lite_content.lite_api.strings import Compliance


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
    if case.case_type.id == CaseTypeEnum.OIEL.id:
        return True
    elif case.case_type.id == CaseTypeEnum.SIEL.id:
        if not (
            Good.objects.filter(
                goods_on_application__application_id=case.id,
                control_list_entries__rating__regex=COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES,
                goods_on_application__licenced_quantity__isnull=False,
            ).exists()
        ):
            return False
        return True
    elif case.case_type.id == CaseTypeEnum.OICL.id:
        return True
    else:
        return False


def get_record_holding_sites_for_case(case_id):
    return set(
        Site.objects.filter(sites_on_application__application_id=case_id).values_list(
            "site_records_located_at_id", flat=True
        )
    )


def generate_compliance_site_case(case: Case):
    # check if case meets conditions required
    if not case_meets_conditions_for_compliance(case):
        return

    # Get record holding sites for the case
    record_holding_sites_id = get_record_holding_sites_for_case(case.id)

    # Get list of record holding sites that do not have a compliance case
    new_compliance_sites = Site.objects.filter(id__in=record_holding_sites_id, compliance__isnull=True).distinct()

    # get a list compliance cases that already exist
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
