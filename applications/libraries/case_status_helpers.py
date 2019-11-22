from static.statuses.enums import CaseStatusEnum


def get_case_statuses(read_only):
    """ Get a list of the case statuses that are read-only. """
    return [
        case_status for case_status, is_read_only in CaseStatusEnum.is_read_only.items() if is_read_only == read_only
    ]


def get_terminal_case_statuses():
    """ Get a list of the case statuses that are terminal. """
    return [case_status for case_status, is_terminal in CaseStatusEnum.is_terminal.items() if is_terminal]
