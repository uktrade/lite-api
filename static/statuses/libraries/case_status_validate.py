from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus


def case_status_draft(status):
    if isinstance(status, CaseStatus):
        return status.status == CaseStatusEnum.DRAFT
    return status == CaseStatusEnum.DRAFT
