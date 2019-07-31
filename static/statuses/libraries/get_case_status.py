from conf.exceptions import NotFoundError
from static.statuses.models import CaseStatus


def get_case_status(case_status_enum):
    if len(case_status_enum) == 2:
        case_status_enum = case_status_enum[0]

    try:
        return CaseStatus.objects.get(id=case_status_enum)
    except CaseStatus.DoesNotExist:
        raise NotFoundError({'case_status': 'status not found'})
