from cases.libraries.get_case import get_case
from cases.libraries.get_destination import get_destination
from goods.models import Good
from goodstype.helpers import get_goods_type
from organisations.libraries.get_organisation import get_organisation_by_pk


def get_object_of_level(level, pk):
    if level == "good":
        try:
            good = Good.objects.get(pk=pk)
        except Good.DoesNotExist:
            good = get_goods_type(pk)
        return good
    elif level == "case":
        return get_case(pk)
    elif level == "organisation":
        return get_organisation_by_pk(pk)
    elif level == "destination":
        return get_destination(pk)
