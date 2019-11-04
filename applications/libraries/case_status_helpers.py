from static.statuses.enums import CaseStatusEnum


def get_read_only_case_statuses():
    """ Get a list of the case statuses that are read-only. """
    return [case_status for case_status, is_read_only in CaseStatusEnum.is_read_only.items() if is_read_only]


def get_editable_case_statuses():
    """ Get a list of the case statuses that are editable. """
    return [case_status for case_status, is_read_only in CaseStatusEnum.is_read_only.items() if not is_read_only]
