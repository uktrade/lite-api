from cases.libraries.get_case import get_case
from goods.libraries.get_good import get_good
from goodstype.helpers import get_goods_type


def get_object_of_level(level, pk):
    if level == 'Good':
        try:
            good = get_good(pk)
        except:
            good = get_goods_type(pk)
        return good
    elif level == 'Case':
        return get_case(pk)
