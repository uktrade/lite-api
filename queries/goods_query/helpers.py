from conf.exceptions import NotFoundError
from lite_content.lite_api import strings
from queries.goods_query.models import GoodsQuery


def get_goods_query_by_good(good):
    try:
        return GoodsQuery.objects.get(good=good)
    except GoodsQuery.DoesNotExist:
        raise NotFoundError({"GoodsQuery": strings.GoodsQuery.QUERY_NOT_FOUND_ERROR})
