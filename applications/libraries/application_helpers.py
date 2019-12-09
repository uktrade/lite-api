from typing import Optional

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
    if CaseStatusEnum.is_read_only(original_status) or new_status != CaseStatusEnum.APPLICANT_EDITING:
        return (
            f'Setting application status to "{new_status}" when application status '
            f'is "{original_status}" is not allowed.'
        )


def validate_status_can_be_set_by_gov_user(original_status: str, new_status: str) -> Optional[str]:
    if new_status == CaseStatusEnum.APPLICANT_EDITING:
        return f'Setting application status to "{new_status}" is not allowed for GovUsers.'

    if original_status == CaseStatusEnum.APPLICANT_EDITING:
        return (
            f"Setting application status when its existing status is "
            f'"{original_status}" is not allowed for GovUsers.'
        )

