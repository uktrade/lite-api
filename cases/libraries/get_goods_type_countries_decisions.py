from cases.enums import AdviceLevel, AdviceType
from cases.models import Advice
from goodstype.models import GoodsType


def good_type_to_country_decisions(application_pk):
    goods_types_advice = Advice.objects.filter(
        case_id=application_pk, level=AdviceLevel.FINAL, goods_type__isnull=False,
    )
    # TODO reduce queries
    approved_goods_types_ids = goods_types_advice.filter(type=AdviceType.APPROVE).values_list(
        "goods_type_id", flat=True
    )
    refused_goods_types_ids = goods_types_advice.filter(type=AdviceType.REFUSE).values_list("goods_type_id", flat=True)
    approved_and_refused_goods_types = approved_goods_types_ids | refused_goods_types_ids

    approved_countries_advice = Advice.objects.filter(
        case_id=application_pk, level=AdviceLevel.FINAL, country__isnull=False,
    )
    approved_countries_ids = approved_countries_advice.filter(type=AdviceType.APPROVE).values_list(
        "country_id", flat=True
    )
    refused_countries_ids = approved_countries_advice.filter(type=AdviceType.REFUSE).values_list(
        "country_id", flat=True
    )
    approved_and_refused_countries_ids = approved_countries_ids | refused_countries_ids

    goods_types = GoodsType.objects.filter(
        application_id=application_pk, id__in=approved_and_refused_goods_types
    ).prefetch_related("control_list_entries", "countries")

    approved_goods_types_on_destinations = {}
    refused_goods_types_on_destinations = {}

    for goods_type in goods_types:
        for country in goods_type.countries.filter(id__in=approved_and_refused_countries_ids):
            goods_type_approved = goods_type.id in approved_goods_types_ids
            country_approved = country.id in approved_countries_ids

            if goods_type_approved and country_approved:
                dictionary = approved_goods_types_on_destinations
            else:
                dictionary = refused_goods_types_on_destinations

            if goods_type.id not in dictionary.keys():
                dictionary[goods_type.id] = {
                    "id": goods_type.id,
                    "decision": AdviceType.APPROVE if goods_type_approved else AdviceType.REFUSE,
                    "control_list_entries": [clc.rating for clc in goods_type.control_list_entries.all()],
                    "description": goods_type.description,
                    "countries": [
                        {
                            "id": country.id,
                            "name": country.name,
                            "decision": AdviceType.APPROVE if country_approved else AdviceType.REFUSE,
                        }
                    ],
                }
            else:
                dictionary[goods_type.id]["countries"].append(
                    {
                        "id": country.id,
                        "name": country.name,
                        "decision": AdviceType.APPROVE if country_approved else AdviceType.REFUSE,
                    }
                )

    return approved_goods_types_on_destinations, refused_goods_types_on_destinations


def get_required_good_type_to_country_combinations(application_pk):
    approved_goods_types_ids = Advice.objects.filter(
        case_id=application_pk, level=AdviceLevel.FINAL, goods_type__isnull=False, type=AdviceType.APPROVE,
    ).values_list("goods_type_id", flat=True)

    approved_countries_ids = Advice.objects.filter(
        case_id=application_pk, level=AdviceLevel.FINAL, country__isnull=False, type=AdviceType.APPROVE
    ).values_list("country_id", flat=True)

    goods_types = GoodsType.objects.filter(
        application_id=application_pk, id__in=approved_goods_types_ids
    ).prefetch_related("countries")

    return {
        goods_type.id: list(goods_type.countries.filter(id__in=approved_countries_ids).values_list("id", flat=True))
        for goods_type in goods_types
    }
