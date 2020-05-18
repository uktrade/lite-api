from collections import defaultdict

from cases.enums import AdviceType
from cases.models import Advice
from goods.enums import PvGrading
from parties.serializers import PartySerializer
from static.countries.serializers import CountrySerializer


def group_advice(case, advice, user, new_level):
    advice_entities = {entity_field: defaultdict(list) for entity_field in Advice.ENTITY_FIELDS}

    for advice in advice:
        advice_entities[advice.entity_field][advice.entity].append(advice)

    for entity_field in Advice.ENTITY_FIELDS:
        collate_advice(entity_field, new_level, advice_entities[entity_field], case, user)


def collate_advice(entity_field, new_level, collection, case, user):
    for key, advice_list in collection.items():
        denial_reasons = []

        advice = construct_coalesced_advice_values(
            deduplicate_advice(advice_list), case, user, denial_reasons=denial_reasons
        )

        # Set outside the constructor so it can apply only when necessary
        advice.team = user.team
        advice.level = new_level
        setattr(advice, entity_field, key)

        advice.save()
        advice.denial_reasons.set(denial_reasons)


def deduplicate_advice(advice_list):
    """
    This examines each piece of data in a set of advice for an object
    and if there are any exact duplicates it only returns one of them.
    """
    deduplicated = []
    matches = False
    for advice in advice_list:
        for item in deduplicated:
            # Compare each piece of unique advice against the new piece of advice being introduced
            matches = advice.equals(item)
            break
        if not matches:
            deduplicated.append(advice)
    return deduplicated


def construct_coalesced_advice_values(
    deduplicated_advice, case, user, denial_reasons, advice_type=None,
):
    fields = {
        "text": set(),
        "note": set(),
        "pv_grading": set(),
        "proviso": set(),
        "collated_pv_grading": set(),
    }
    break_text = "\n-------\n"
    for advice in deduplicated_advice:
        for denial_reason in advice.denial_reasons.values_list("id", flat=True):
            denial_reasons.append(denial_reason)

        if advice_type:
            if advice_type != advice.type:
                advice_type = AdviceType.CONFLICTING
        else:
            advice_type = advice.type

        for field in fields:
            if getattr(advice, field):
                fields[field].add(getattr(advice, field))

    pv_grading = (
        break_text.join([PvGrading.to_str(pv_grading) for pv_grading in fields["pv_grading"]])
        if fields["pv_grading"]
        else list(fields["collated_pv_grading"])[0]
        if fields["collated_pv_grading"]
        else None
    )

    return Advice(
        text=break_text.join(fields["text"]),
        case=case,
        note=break_text.join(fields["note"]),
        proviso=break_text.join(fields["proviso"]),
        user=user,
        type=advice_type,
        collated_pv_grading=pv_grading,
    )


def get_serialized_entities_from_final_advice_on_case(case, advice_type=None):
    """
    Returns a dictionary containing the entity type as the key and the serialized entity/entities as the value.
    E.G.
    {"goods": [{"id": ...,},], "end_user": {"id": ...,},]
    """
    from goods.serializers import GoodCreateSerializer
    from goodstype.serializers import GoodsTypeSerializer

    advice_entity_field_map = {
        "good": {"serializer": GoodCreateSerializer, "case_relationship": "goods"},
        "goods_type": {"serializer": GoodsTypeSerializer, "case_relationship": "goods_types"},
        "country": {"serializer": CountrySerializer, "case_relationship": "countries"},
        "end_user": {"serializer": PartySerializer, "case_relationship": "end_user"},
        "consignee": {"serializer": PartySerializer, "case_relationship": "consignee"},
        "ultimate_end_user": {"serializer": PartySerializer, "case_relationship": "ultimate_end_users"},
        "third_party": {"serializer": PartySerializer, "case_relationship": "third_parties"},
    }

    final_advice = Advice.objects.distinct(*Advice.ENTITY_FIELDS).filter(case=case)

    if advice_type:
        final_advice = final_advice.filter(type=advice_type)

    final_advice_entities = defaultdict(list)

    for advice in final_advice:
        serializer = advice_entity_field_map[advice.entity_field]["serializer"]
        case_relationship = advice_entity_field_map[advice.entity_field]["case_relationship"]
        data = serializer(advice.entity).data

        # If the case_relationship is many-to-many, append the data to a list
        # This is determined by comparing the singular field expression (advice.entity_field) to case_relationship
        if case_relationship != advice.entity_field:
            final_advice_entities[case_relationship].append(data)
        else:
            final_advice_entities[case_relationship] = data

    return final_advice_entities
