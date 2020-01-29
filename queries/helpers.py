from conf.exceptions import NotFoundError
from queries.goods_query.models import GoodsQuery
from queries.end_user_advisories.models import EndUserAdvisoryQuery


def get_exporter_query(pk):
    """
    Returns either a Control List Classification Query or
    a End User Classification Query depending on the PK given
    """
    try:
        return GoodsQuery.objects.get(pk=pk)
    except GoodsQuery.DoesNotExist:
        try:
            return EndUserAdvisoryQuery.objects.get(pk=pk)
        except EndUserAdvisoryQuery.DoesNotExist:
            raise NotFoundError({"query": "Query not found - " + str(pk)})
