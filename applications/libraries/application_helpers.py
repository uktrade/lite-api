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
    if new_status == CaseStatusEnum.SUBMITTED:
        return 'Setting application status to "{}" is not allowed.'.format(str(new_status))
    if isinstance(user, ExporterUser):
        if original_status != CaseStatusEnum.SUBMITTED and new_status == CaseStatusEnum.APPLICANT_EDITING:
            return 'Setting application status to "{}" when application status is "{}" is not allowed.'.format(
                str(new_status), str(original_status)
            )
    else:
        if new_status == CaseStatusEnum.APPLICANT_EDITING:
            return 'Setting application status to "{}" is not allowed for GovUsers.'.format(str(new_status))
        elif original_status == CaseStatusEnum.APPLICANT_EDITING:
            return 'Setting application status when its existing status is "{}" is not allowed for GovUsers.'.format(
                str(original_status)
            )
