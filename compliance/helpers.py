from django.db.models import When, Case as db_case, F
from django.utils import timezone

from cases.enums import CaseTypeEnum
from cases.models import Case
from compliance.models import ComplianceSiteCase
from organisations.models import Site
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


def generate_compliance(case: Case):
    # check if case meets conditions required
    if case.case_type.id == CaseTypeEnum.OIEL.id:
        pass
    elif case.case_type.id == CaseTypeEnum.SIEL.id:
        # TODO: Check that the control code is ML21 ML22 or dual list
        pass
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
    new_compliance_sites = set(Site.objects.filter(id__in=record_holding_sites_id, compliance__isnull=True))

    if not new_compliance_sites:
        return None

    for site in new_compliance_sites:
        ComplianceSiteCase(
            site=site,
            status=get_case_status_by_status(CaseStatusEnum.DRAFT),
            organisation_id=case.organisation_id,
            case_type_id=CaseTypeEnum.COMPLIANCE.id,
            submitted_at=timezone.now(),
        ).save()

    # TODO: bulk create audits for creating and new licence on compliance site.
