from typing import Optional

from applications.models import BaseApplication, StandardApplication
from applications.serializers import StandardApplicationSerializer, OpenApplicationSerializer
from conf.exceptions import NotFoundError
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status_enum
from users.models import BaseUser, ExporterUser


def get_serializer_for_application(application: BaseApplication, many=False):
    if isinstance(application, StandardApplication):
        return StandardApplicationSerializer(application, many=many)
    else:
        return OpenApplicationSerializer(application, many=many)


def optional_str_to_bool(optional_string: str):
    if optional_string is None:
        return None
    elif optional_string.lower() == 'true':
        return True
    elif optional_string.lower() == 'false':
        return False
    else:
        raise ValueError('You provided ' + optional_string + ', while the allowed values are None, "true" or "false"')


def validate_status_can_be_set(original_status: CaseStatusEnum,
                               new_status: CaseStatusEnum,
                               user: BaseUser) -> Optional[str]:
    try:
        get_case_status_from_status_enum(new_status)
    except NotFoundError:
        return 'Status not found.'

    if isinstance(user, ExporterUser):
        if original_status != CaseStatusEnum.SUBMITTED and new_status == CaseStatusEnum.APPLICANT_EDITING:
            return f'Setting application status to "{str(new_status)}" when application status is ' \
                f'"{str(original_status)}" is not allowed.'

        if new_status == CaseStatusEnum.SUBMITTED:
            return f'Setting application status to "{str(new_status)}" is not allowed.'
    else:
        if new_status == CaseStatusEnum.APPLICANT_EDITING:
            return f'Setting application status to "{str(new_status)}" is not allowed for GovUsers.'
        elif original_status == CaseStatusEnum.APPLICANT_EDITING:
            return f'Setting application status when its existing status is ' \
                f'"{str(original_status)}" is not allowed for GovUsers.'
