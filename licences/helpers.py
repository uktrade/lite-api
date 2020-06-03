from cases.enums import AdviceType
from cases.models import Advice


def get_approved_goods_on_application(application):
    approved_goods = Advice.objects.filter(
        case_id=application.id, type__in=[AdviceType.APPROVE, AdviceType.PROVISO]
    ).values_list("good", flat=True)
    return application.goods.filter(good_id__in=approved_goods)


def get_approved_goods_types(application):
    approved_goods = Advice.objects.filter(
        case_id=application.id, type__in=[AdviceType.APPROVE, AdviceType.PROVISO]
    ).values_list("goods_type", flat=True)
    return application.goods_type.filter(id__in=approved_goods)
