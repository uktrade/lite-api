from typing import List, Dict

from common.cache import lite_cache, Key
from static.statuses.enums import CaseStatusEnum


@lite_cache(Key.STATUS_LIST)
def get_case_status_list() -> List[Dict]:
    return CaseStatusEnum.as_list()
