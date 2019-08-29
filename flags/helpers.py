from cases.libraries.get_case import get_case
from goods.models import Good
from goodstype.helpers import get_goods_type


def get_object_of_level(level, pk):
    if level == 'Good':
        try:
            good = Good.objects.get(pk=pk)
        except Good.DoesNotExist:
            good = get_goods_type(pk)
        return good
    elif level == 'Case':
        return get_case(pk)
