from conf.exceptions import NotFoundError
from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus


def get_status_from_case_status(case_status):
    return [x for x in CaseStatusEnum.choices if x[0] == case_status][0][1]


def get_case_status_from_status_enum(case_status):
    # if passed tuple
    if case_status and len(case_status) == 2:
        case_status = case_status[0]

    try:
        return CaseStatus.objects.get(status=case_status)
    except CaseStatus.DoesNotExist:
        raise NotFoundError({'case_status': 'status not found'})


def get_case_status_from_pk(pk):
    try:
        return CaseStatus.objects.get(pk=pk)
    except CaseStatus.DoesNotExist:
        raise NotFoundError({'case_status': 'status not found'})
