from django.db.models import Sum, Max, F

from cases.enums import AdviceType, AdviceLevel
from goods.models import Good
from licences.enums import LicenceStatus
from licences.models import GoodOnLicence, Licence
from static.control_list_entries.serializers import ControlListEntrySerializer


def get_goods_on_licence(licence, include_control_list_entries=False):
    goods_on_licence = (
        GoodOnLicence.objects.filter(
            licence__application=licence.application,
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
            "id": str(good["id"]),
            "good_id": str(good["good_id"]),
            "unit": good["unit"],
            "usage": good["usage_total"],
            "usage_licenced": good["usage_licenced"],
            "usage_applied_for": good["usage_applied_for"],
            "value": good["value"],
            "description": good["description"],
            "licenced_value": float(good["value"]) * float(good["usage_licenced"]) if good["value"] and good["usage_licenced"] else None,
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
            str(good.id): ControlListEntrySerializer(good.control_list_entries.all(), many=True).data
            for good in Good.objects.filter(id__in=[gol["good_id"] for gol in goods_on_licence]).prefetch_related(
                "control_list_entries"
            )
        }

        for good in goods:
            good["control_list_entries"] = control_list_entries[good["good_id"]]

    return goods


def get_case_licences(case):
    licences = Licence.objects.prefetch_related("goods", "goods__good", "goods__good__good", "goods__good__good__control_list_entries").filter(application=case)
    return [
        {
            "id": str(licence.id),
            "reference_code": licence.reference_code,
            "duration": licence.duration,
            "status": LicenceStatus.human_readable(licence.status),
            "goods": [
                {
                    "description": licence_good.good.good.description,
                    "control_list_entries": ControlListEntrySerializer(licence_good.good.good.control_list_entries.all(), many=True).data,
                    "quantity": licence_good.quantity,
                    "usage": licence_good.usage
                } for licence_good in licence.goods.all()
            ]
        } for licence in licences
    ]
