from typing import List, Dict

from cases.enums import CaseTypeExtendedEnum
from cases.views.search.queue import SearchQueue
from static.statuses.enums import CaseStatusEnum


def get_case_status_list() -> List[Dict]:
    return CaseStatusEnum.as_list()


def get_case_type_reference_list() -> List[Dict]:
    return CaseTypeExtendedEnum.Type.as_list()


def get_case_type_sub_type_list() -> List[Dict]:
    return CaseTypeExtendedEnum.Type.as_list()


def get_case_type_type_list() -> List[Dict]:
    return CaseTypeExtendedEnum.Type.as_list()


def get_search_queues(user):
    return SearchQueue.all(user=user)
