from conf.exceptions import NotFoundError
from queries.goods_query.models import GoodsQuery


def get_clc_query_by_good(good):
    try:
        return GoodsQuery.objects.get(good=good)
    except GoodsQuery.DoesNotExist:
        raise NotFoundError({"control_list_classification": "Control List Classification not found"})
