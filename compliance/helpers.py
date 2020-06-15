import csv
import re

from django.db.models import When, Case as db_case, F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from audit_trail.enums import AuditType
from audit_trail.models import Audit
from cases.enums import CaseTypeEnum
from cases.models import Case
from compliance.models import ComplianceSiteCase
from goods.models import Good
from organisations.models import Site
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.enums import SystemUser
from users.models import BaseUser
from licences.models import Licence
from lite_content.lite_api.strings import Compliance


def generate_compliance(case: Case):
    # check if case meets conditions required
    if case.case_type.id == CaseTypeEnum.OIEL.id:
        pass
    elif case.case_type.id == CaseTypeEnum.SIEL.id:
        if not (
            Good.objects.filter(
                goods_on_application__application_id=case.id,
                control_list_entries__rating__regex="(^[0-9][DE].*$)|(^ML21.*$)|(^ML22.*$)",
            ).exists()
        ):
            return None
    elif case.case_type.id == CaseTypeEnum.OICL.id:
        pass
    else:
        return None

    # Get record holding sites the case
    record_holding_sites_id = set(
        Site.objects.filter(sites_on_application__application_id=case.id)
        .annotate(
            record_site=db_case(
                When(site_records_located_at__isnull=False, then=F("site_records_located_at")), default=F("id")
            )
        )
        .values_list("record_site", flat=True)
    )

    # Get list of record holding sites that do not relate to compliance case
    new_compliance_sites = set(Site.objects.filter(id__in=record_holding_sites_id, compliance__isnull=True).distinct())
    existing_compliance_cases = set(
        Case.objects.filter(compliancesitecase__site_id__in=record_holding_sites_id).distinct()
    )

    audits = []
    system_user = BaseUser.objects.get(id=SystemUser.id)
    for comp_case in existing_compliance_cases:
        audits.append(
            Audit(
                actor=system_user,
                verb=AuditType.COMPLIANCE_SITE_CASE_NEW_LICENCE,
                target=comp_case,
                payload={"case_reference": case.reference_code},
            )
        )

    if not new_compliance_sites:
        Audit.objects.bulk_create(audits)
        return None

    for site in new_compliance_sites:
        comp_case = ComplianceSiteCase(
            site=site,
            status=get_case_status_by_status(CaseStatusEnum.OPEN),
            organisation_id=case.organisation_id,
            case_type_id=CaseTypeEnum.COMPLIANCE.id,
            submitted_at=timezone.now(),
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
