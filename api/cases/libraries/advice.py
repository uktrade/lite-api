from collections import defaultdict

from api.cases.enums import AdviceType
from api.cases.models import Advice
from api.goods.enums import PvGrading


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
        "footnote": set(),
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
        footnote=break_text.join(fields["footnote"]),
        footnote_required=len(fields["footnote"]) > 0,
    )
