from static.statuses.models import CaseStatus


def get_case_statuses(read_only):
    """ Get a list of the case statuses that are read-only. """
    case_statuses = CaseStatus.objects.filter(is_read_only=read_only).values_list("status", flat=True)
    return case_statuses
