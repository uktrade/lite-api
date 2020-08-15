from django.utils import timezone

from api.cases.tasks import get_application_target_sla
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


def get_case_statuses(read_only):
    """ Get a list of the case statuses that are read-only. """
    if read_only:
        return CaseStatusEnum.read_only_statuses()
    else:
        return [status for status, value in CaseStatusEnum.choices if not CaseStatusEnum.is_read_only(status)]


def submit_application(application):
    application.status = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
    application.submitted_at = timezone.now()
    application.sla_remaining_days = get_application_target_sla(application.case_type.sub_type)
    application.sla_days = 0
    application.save()
