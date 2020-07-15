from cases.enums import AdviceLevel, AdviceType
from cases.models import Advice, GoodCountryDecision
from goodstype.models import GoodsType


def get_existing_good_type_to_country_decisions(case_pk):
    """
    Get all existing GoodCountryDecisions for a case
    """
    goods_type_countries_decisions = GoodCountryDecision.objects.filter(case_id=case_pk).values(
        "goods_type_id", "country_id", "approve"
    )
    return {f"{item['goods_type_id']}.{item['country_id']}": item["approve"] for item in goods_type_countries_decisions}


def _get_country_on_goods_type_context(country, goods_type, approved, goods_type_countries_decisions):
    """
    Get the dictionary context for a country on a good.
    This includes the country name, decision for the country
    and value if a decision for this combination already exists
    """
    existing_decision = goods_type_countries_decisions.get(f"{goods_type.id}.{country.id}")
    if existing_decision is not None:
        existing_decision = AdviceType.APPROVE if existing_decision else AdviceType.REFUSE

    return {
        "id": country.id,
        "name": country.name,
        "decision": AdviceType.APPROVE if approved else AdviceType.REFUSE,
        "value": existing_decision,
    }


def good_type_to_country_decisions(application_pk):
    """
    Get data for the Good on Country matrix page.
    This divides all good on country combinations into approved
    (where both good & country are approved at the final advice level)
    and refused (good and/or country is refused).
    Returns the approved and refused dictionaries
    """
    goods_types_advice = Advice.objects.filter(
        case_id=application_pk,
        level=AdviceLevel.FINAL,
        goods_type__isnull=False,
        type__in=[AdviceType.APPROVE, AdviceType.REFUSE],
    ).values("goods_type_id", "type")
    approved_goods_types_ids = [
        item["goods_type_id"] for item in goods_types_advice if item["type"] == AdviceType.APPROVE
    ]
    refused_goods_types_ids = [
        item["goods_type_id"] for item in goods_types_advice if item["type"] == AdviceType.REFUSE
    ]
    approved_and_refused_goods_types = approved_goods_types_ids + refused_goods_types_ids

    countries_advice = Advice.objects.filter(
        case_id=application_pk,
        level=AdviceLevel.FINAL,
        country__isnull=False,
        type__in=[AdviceType.APPROVE, AdviceType.REFUSE],
    ).values("country_id", "type")
    approved_countries_ids = [item["country_id"] for item in countries_advice if item["type"] == AdviceType.APPROVE]
    refused_countries_ids = [item["country_id"] for item in countries_advice if item["type"] == AdviceType.REFUSE]
    approved_and_refused_countries_ids = approved_countries_ids + refused_countries_ids

    goods_types = (
        GoodsType.objects.filter(application_id=application_pk, id__in=approved_and_refused_goods_types)
        .prefetch_related("control_list_entries", "countries")
        .order_by("created_at")
    )

    goods_type_countries_decisions = get_existing_good_type_to_country_decisions(application_pk)
    approved_goods_types_on_destinations = {}
    refused_goods_types_on_destinations = {}

    for goods_type in goods_types:
        for country in goods_type.countries.filter(id__in=approved_and_refused_countries_ids).order_by("name"):
            goods_type_approved = goods_type.id in approved_goods_types_ids
            country_approved = country.id in approved_countries_ids

            # Add to approve or refuse dictionary depending on whether both good & country is approved
            if goods_type_approved and country_approved:
                dictionary = approved_goods_types_on_destinations
            else:
                dictionary = refused_goods_types_on_destinations

            if goods_type.id not in dictionary.keys():
                dictionary[goods_type.id] = {
                    "id": goods_type.id,
                    "decision": AdviceType.APPROVE if goods_type_approved else AdviceType.REFUSE,
                    "control_list_entries": [
                        {"rating": clc.rating, "text": clc.text} for clc in goods_type.control_list_entries.all()
                    ],
                    "description": goods_type.description,
                    "countries": [
                        _get_country_on_goods_type_context(
                            country, goods_type, country_approved, goods_type_countries_decisions
                        )
                    ],
                }
            else:
                dictionary[goods_type.id]["countries"].append(
                    _get_country_on_goods_type_context(
                        country, goods_type, country_approved, goods_type_countries_decisions
                    )
                )

    return approved_goods_types_on_destinations, refused_goods_types_on_destinations


def get_required_good_type_to_country_combinations(application_pk):
    """
    Get all required good on country combinations.
    (both good & country are approved at the final advice level)
    """
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
