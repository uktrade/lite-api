from conf.exceptions import NotFoundError
from static.statuses.models import CaseStatus


def get_case_status_by_id(case_status_enum):
    try:
        return CaseStatus.objects.get(id=case_status_enum)
    except CaseStatus.DoesNotExist:
        raise NotFoundError({'case_status': 'status not found'})
