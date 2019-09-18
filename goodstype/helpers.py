from django.http import Http404

from goodstype.models import GoodsType


def get_goods_type(pk):
    try:
        return GoodsType.objects.get(pk=pk)
    except GoodsType.DoesNotExist:
        raise Http404


def get_goods_types_from_case(case):
    if case.query:
        return []
    return GoodsType.objects.filter(object_id=case.application.id)
