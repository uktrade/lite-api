from cases.enums import AdviceType
from cases.models import Advice

from applications.models import StandardApplication, OpenApplication


def get_approved_goods_on_application(application: StandardApplication):
    approved_goods = Advice.objects.filter(
        case_id=application.id, type__in=[AdviceType.APPROVE, AdviceType.PROVISO]
    ).values_list("good", flat=True)
    return application.goods.filter(good_id__in=approved_goods)


def get_approved_goods_types(application: OpenApplication):
    approved_goods = Advice.objects.filter(
        case_id=application.id, type__in=[AdviceType.APPROVE, AdviceType.PROVISO]
    ).values_list("goods_type", flat=True)
    return application.goods_type.filter(id__in=approved_goods)
