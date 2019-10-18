from django.http import Http404

from goodstype.models import GoodsType


def get_goods_type(pk):
    try:
        return GoodsType.objects.get(pk=pk)
    except GoodsType.DoesNotExist:
        raise Http404
