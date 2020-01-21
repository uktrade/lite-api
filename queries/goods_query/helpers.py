from conf.exceptions import NotFoundError
from flags.enums import SystemFlags
from flags.models import Flag
from lite_content.lite_api import strings
from queries.goods_query.models import GoodsQuery
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


def get_goods_query_by_good(good):
    try:
        return GoodsQuery.objects.get(good=good)
    except GoodsQuery.DoesNotExist:
        raise NotFoundError({"GoodsQuery": strings.GoodsQuery.QUERY_NOT_FOUND_ERROR})


def update_goods_query_status(query: GoodsQuery):
    """
    Ascertain if the Goods Query status should be updated to Finalised or Submitted
    """
    flags = [
        SystemFlags.GOOD_CLC_QUERY_ID,
        SystemFlags.GOOD_PV_GRADING_QUERY_ID,
    ]

    if query.flags.filter(id__in=flags):
        return get_case_status_by_status(CaseStatusEnum.SUBMITTED)
    else:
        return get_case_status_by_status(CaseStatusEnum.FINALISED)
