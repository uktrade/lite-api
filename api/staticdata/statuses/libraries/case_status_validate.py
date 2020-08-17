from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus


def is_case_status_draft(status):
    if isinstance(status, CaseStatus):
        return status.status == CaseStatusEnum.DRAFT
    return status == CaseStatusEnum.DRAFT
