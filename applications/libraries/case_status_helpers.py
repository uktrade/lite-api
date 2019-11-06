from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus


def get_case_statuses(is_read_only):
    """ Get a list of the case statuses that are read-only. """
    return CaseStatus.objects.filter(is_read_only=is_read_only).values_list('status', flat=True)
