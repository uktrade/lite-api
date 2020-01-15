from conf.exceptions import NotFoundError
from flags.enums import SystemFlags
from flags.models import Flag
from queries.goods_query.models import GoodsQuery
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


def get_clc_query_by_good(good):
    try:
        return GoodsQuery.objects.get(good=good)
    except GoodsQuery.DoesNotExist:
        raise NotFoundError({"GoodsQuery": "Goods query not found"})


def is_goods_query_finished(query: GoodsQuery):
    flags = [
        Flag.objects.get(id=SystemFlags.GOOD_CLC_QUERY_ID),
        Flag.objects.get(id=SystemFlags.GOOD_PV_GRADING_QUERY_ID),
    ]

    if query.objects.filter(flags__id__in=flags):
        return get_case_status_by_status(CaseStatusEnum.SUBMITTED)
    else:
        return get_case_status_by_status(CaseStatusEnum.FINALISED)
