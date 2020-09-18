from api.core.exceptions import NotFoundError
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus


def get_status_value_from_case_status_enum(case_status):
    if CaseStatusEnum.is_system_status(case_status):
        return case_status
    return [x for x in CaseStatusEnum.choices if x[0] == case_status][0][1]


def get_case_status_by_status(status):
    instance = CaseStatus.objects.filter(status=status).order_by("id").first()
    if not instance:
        raise NotFoundError({"status": [f"{status} isn't a valid status"]})

    return instance


def get_case_status_by_pk(pk):
    try:
        return CaseStatus.objects.get(pk=pk)
    except CaseStatus.DoesNotExist:
        raise NotFoundError({"status": "status not found"})
