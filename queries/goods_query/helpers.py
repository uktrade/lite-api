from conf.exceptions import NotFoundError
from flags.enums import SystemFlags
from lite_content.lite_api import strings
from queries.goods_query.models import GoodsQuery
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


def get_goods_query_by_good(good):
    try:
        return GoodsQuery.objects.get(good=good)
    except GoodsQuery.DoesNotExist:
        raise NotFoundError({"GoodsQuery": strings.GoodsQuery.QUERY_NOT_FOUND_ERROR})
