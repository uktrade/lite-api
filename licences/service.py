from django.db.models import Sum, Max, F

from cases.enums import AdviceType, AdviceLevel
from goods.models import Good
from licences.models import GoodOnLicence
from static.control_list_entries.serializers import ControlListEntrySerializer


def get_goods_on_licence(licence, include_control_list_entries=False):
    goods_on_licence = (
        GoodOnLicence.objects.filter(
            licence=licence,
            good__good__advice__type__in=[AdviceType.APPROVE, AdviceType.PROVISO],
            good__good__advice__case_id=licence.application.id,
            good__good__advice__good_id__isnull=False,
            good__good__advice__level=AdviceLevel.FINAL,
        )
        .distinct()
        .values("good")
        .annotate(
            usage_total=Sum("usage"),
            usage_licenced=Max("quantity"),
            usage_applied_for=F("good__quantity"),
            id=F("good__id"),
            advice_type=F("good__good__advice__type"),
            advice_text=F("good__good__advice__text"),
            advice_proviso=F("good__good__advice__proviso"),
            good_id=F("good__good__id"),
            unit=F("good__unit"),
            value=F("good__value"),
            description=F("good__good__description"),
        )
    )

    goods = [
        {
            "id": good["id"],
            "good_id": good["good_id"],
            "unit": good["unit"],
            "usage_total": good["usage_total"],
            "usage_licenced": good["usage_licenced"],
            "usage_applied_for": good["usage_applied_for"],
            "value": good["value"],
            "advice": {
                "type": AdviceType.as_representation(good["advice_type"]),
                "text": good["advice_text"],
                "proviso": good["advice_proviso"],
            },
        }
        for good in goods_on_licence
    ]

    if include_control_list_entries:
        control_list_entries = {
            good.id: ControlListEntrySerializer(good.control_list_entries.all(), many=True).data
            for good in Good.objects.filter(id__in=[gol["good_id"] for gol in goods_on_licence]).prefetch_related(
                "control_list_entries"
            )
        }

        for good in goods:
            good["control_list_entries"] = control_list_entries[good["good_id"]]

    return goods
