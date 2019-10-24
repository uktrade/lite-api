from conf.exceptions import NotFoundError
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus


def get_status_value_from_case_status_enum(case_status):
    return [x for x in CaseStatusEnum.choices if x[0] == case_status][0][1]


def get_case_status_by_status(status):
    try:
        return CaseStatus.objects.get(status=status)
    except CaseStatus.DoesNotExist:
        raise NotFoundError({'case_status': 'status not found'})


def get_case_status_by_pk(pk):
    try:
        return CaseStatus.objects.get(pk=pk)
    except CaseStatus.DoesNotExist:
        raise NotFoundError({'case_status': 'status not found'})
