from static.statuses.enums import CaseStatusEnum


def get_case_statuses(read_only):
    """ Get a list of the case statuses that are read-only. """
    if read_only:
        return CaseStatusEnum.read_only_statuses
    else:
        return [
            status for status, value in CaseStatusEnum.choices if not CaseStatusEnum.is_read_only(status)
        ]
