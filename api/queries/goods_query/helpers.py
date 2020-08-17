from api.core.exceptions import NotFoundError
from lite_content.lite_api import strings
from api.queries.goods_query.models import GoodsQuery
from api.static.statuses.enums import CaseStatusEnum
from api.static.statuses.libraries.get_case_status import get_case_status_by_status


def get_goods_query_by_good(good):
    try:
        return GoodsQuery.objects.get(good=good)
    except GoodsQuery.DoesNotExist:
        raise NotFoundError({"GoodsQuery": strings.GoodsQuery.QUERY_NOT_FOUND_ERROR})


def get_starting_status(is_clc_required):
    if is_clc_required:
        return get_case_status_by_status(CaseStatusEnum.CLC)
    else:
        return get_case_status_by_status(CaseStatusEnum.PV)
