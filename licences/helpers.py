from cases.enums import AdviceType
from cases.models import Advice
from django.db import transaction

from licences.models import Licence
from string import ascii_uppercase


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


@transaction.atomic
def get_reference_code(application_reference):
    # Needs to lock so that 2 Licences don't get the same reference code
    total_reference_codes = (
        Licence.objects.filter(reference_code__icontains=application_reference).select_for_update().count()
    )
    return (
        f"{application_reference}/{ascii_uppercase[total_reference_codes-1]}"
        if total_reference_codes != 0
        else application_reference
    )
