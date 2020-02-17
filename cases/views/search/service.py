from typing import List, Dict

from django.db.models import Value
from django.db.models.functions import Concat

from cases.enums import CaseTypeTypeEnum
from cases.views.search.queue import SearchQueue
from static.statuses.enums import CaseStatusEnum
from users.enums import UserStatuses
from users.models import GovUser


def get_case_status_list() -> List[Dict]:
    return CaseStatusEnum.as_list()


def get_case_type_type_list() -> List[Dict]:
    return CaseTypeTypeEnum.as_list()


def get_search_queues(user):
    return SearchQueue.all(user=user)


def get_gov_users_list():
    return [
        {"key": full_name.lower(), "value": full_name}
        for full_name in GovUser.objects.filter(status=UserStatuses.ACTIVE)
        .annotate(full_name=Concat("first_name", Value(" "), "last_name"))
        .values_list("full_name", flat=True)
    ]
