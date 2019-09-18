from conf.exceptions import NotFoundError
from static.statuses.models import CaseStatus


def get_case_status_from_status(case_status):
    # if passed tuple
    if len(case_status) == 2:
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
