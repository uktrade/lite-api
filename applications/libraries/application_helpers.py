from typing import Optional

from applications.models import BaseApplication, StandardApplication, OpenApplication, HmrcQuery
from applications.serializers.hmrc import HmrcQueryViewSerializer
from applications.serializers.serializers import StandardApplicationViewSerializer, OpenApplicationViewSerializer
from static.statuses.enums import CaseStatusEnum


def optional_str_to_bool(optional_string: str):
    if optional_string is None:
        return None
    elif optional_string.lower() == 'true':
        return True
    elif optional_string.lower() == 'false':
        return False
    else:
        raise ValueError('You provided ' + optional_string + ', while the allowed values are None, "true" or "false"')


def validate_status_can_be_set_by_exporter_user(original_status: str, new_status: str) -> Optional[str]:
    if original_status != CaseStatusEnum.SUBMITTED and new_status == CaseStatusEnum.APPLICANT_EDITING:
        return f'Setting application status to "{new_status}" when application status is ' \
            f'"{original_status}" is not allowed.'

    if new_status == CaseStatusEnum.SUBMITTED:
        return f'Setting application status to "{new_status}" is not allowed.'


def validate_status_can_be_set_by_gov_user(original_status: str, new_status: str) -> Optional[str]:
    if new_status == CaseStatusEnum.APPLICANT_EDITING:
        return f'Setting application status to "{new_status}" is not allowed for GovUsers.'

    if original_status == CaseStatusEnum.APPLICANT_EDITING:
        return f'Setting application status when its existing status is ' \
            f'"{original_status}" is not allowed for GovUsers.'
