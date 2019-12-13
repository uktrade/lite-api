from typing import Optional

from conf.constants import GovPermissions
from conf.permissions import assert_user_has_permission
from static.statuses.enums import CaseStatusEnum


def optional_str_to_bool(optional_string: str):
    if optional_string is None:
        return None
    elif optional_string.lower() == "true":
        return True
    elif optional_string.lower() == "false":
        return False
    else:
        raise ValueError("You provided " + optional_string + ', while the allowed values are None, "true" or "false"')


def validate_status_can_be_set_by_exporter_user(original_status: str, new_status: str) -> Optional[str]:
    error_message_template = 'Setting application status to "{}" when application status "{}" is not allowed.'

    if new_status == CaseStatusEnum.WITHDRAWN:
        if CaseStatusEnum.is_terminal(original_status):
            return error_message_template.format(new_status, original_status)
        return
    elif CaseStatusEnum.is_read_only(original_status) or new_status != CaseStatusEnum.APPLICANT_EDITING:
        return error_message_template.format(new_status, original_status)


def validate_status_can_be_set_by_gov_user(user, original_status: str, new_status: str) -> Optional[str]:
    """ Validate that a status can be set by a gov user. Gov users can not set a case's status to
    Applicant editing. They also cannot set a case's status to `Finalised` or open a closed case
    without additional permissions.
    """
    if new_status == CaseStatusEnum.APPLICANT_EDITING:
        return f'Setting application status to "{new_status}" is not allowed for GovUsers.'

    if CaseStatusEnum.is_terminal(original_status) and not assert_user_has_permission(
        user, GovPermissions.REOPEN_CLOSED_CASES
    ):
        return f'Setting a terminal application to "{new_status}" is not allow for GovUsers without permission.'

    if new_status == CaseStatusEnum.FINALISED and not assert_user_has_permission(
        user, GovPermissions.MANAGE_FINAL_ADVICE
    ):
        return f'Setting application status to "{new_status}" is not allow for GovUsers without permission.'
