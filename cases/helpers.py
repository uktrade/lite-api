from collections import defaultdict

from cases.enums import AdviceType
from goods.enums import PvGrading
from goods.models import Good
from static.countries.models import Country
from users.models import GovUser, GovNotification


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
    deduplicated_advice, case, advice_class, user, denial_reasons, advice_type=None,
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

    return advice_class(
        text=break_text.join(fields["text"]),
        case=case,
        note=break_text.join(fields["note"]),
        proviso=break_text.join(fields["proviso"]),
        user=user,
        type=advice_type,
        collated_pv_grading=pv_grading,
    )


def assign_field(application_field, advice, key):
    from goodstype.models import GoodsType

    if application_field == "good":
        advice.good = Good.objects.get(pk=key)
    elif application_field == "end_user":
        advice.end_user = key
    elif application_field == "country":
        advice.country = Country.objects.get(pk=key)
    elif application_field == "ultimate_end_user":
        advice.ultimate_end_user = key
    elif application_field == "goods_type":
        advice.goods_type = GoodsType.objects.get(pk=key)
    elif application_field == "consignee":
        advice.consignee = key
    elif application_field == "third_party":
        advice.third_party = key


def collate_advice(application_field, collection, case, user, advice_class):
    for key, advice_list in collection.items():
        denial_reasons = []

        advice = construct_coalesced_advice_values(
            deduplicate_advice(advice_list), case, advice_class, user, denial_reasons=denial_reasons
        )

        # Set outside the constructor so it can apply only when necessary
        advice.team = user.team

        assign_field(application_field, advice, key)

        advice.save()
        advice.denial_reasons.set(denial_reasons)


def create_grouped_advice(case, request, advice, level):
    """
    Takes the advice from a case and combines it against each field to the level specified (team or final)
    """
    end_users = defaultdict(list)
    ultimate_end_users = defaultdict(list)
    goods = defaultdict(list)
    goods_types = defaultdict(list)
    countries = defaultdict(list)
    consignees = defaultdict(list)
    third_parties = defaultdict(list)

    for advice in advice:
        if advice.end_user:
            end_users[advice.end_user].append(advice)
        elif advice.country:
            countries[advice.country.id].append(advice)
        elif advice.good:
            goods[advice.good.id].append(advice)
        elif advice.ultimate_end_user:
            ultimate_end_users[advice.ultimate_end_user].append(advice)
        elif advice.goods_type:
            goods_types[advice.goods_type.id].append(advice)
        elif advice.consignee:
            consignees[advice.consignee].append(advice)
        elif advice.third_party:
            third_parties[advice.third_party].append(advice)

    collate_advice("end_user", end_users, case, request.user, level)
    collate_advice("good", goods, case, request.user, level)
    collate_advice("country", countries, case, request.user, level)
    collate_advice("ultimate_end_user", ultimate_end_users, case, request.user, level)
    collate_advice("goods_type", goods_types, case, request.user, level)
    collate_advice("consignee", consignees, case, request.user, level)
    collate_advice("third_party", third_parties, case, request.user, level)


def get_assigned_to_user_case_ids(user: GovUser):
    from cases.models import CaseAssignment

    return CaseAssignment.objects.filter(users=user).values_list("case__id", flat=True)


def get_users_assigned_to_case(case_assignments):
    users = []

    for case_assignment in case_assignments:
        queue_users = [
            {"first_name": first_name, "last_name": last_name, "email": email, "queue": case_assignment.queue.name,}
            for first_name, last_name, email in case_assignment.users.values_list("first_name", "last_name", "email")
        ]

        users.extend(queue_users)
    return users


def get_assigned_as_case_officer_case_ids(user: GovUser):
    from cases.models import Case

    return Case.objects.filter(case_officer=user).values_list("id", flat=True)


def get_updated_case_ids(user: GovUser):
    """
    Get the cases that have raised notifications when updated by an exporter
    """
    assigned_to_user_case_ids = get_assigned_to_user_case_ids(user)
    assigned_as_case_officer_case_ids = get_assigned_as_case_officer_case_ids(user)
    cases = assigned_to_user_case_ids.union(assigned_as_case_officer_case_ids)

    return GovNotification.objects.filter(user=user, case__id__in=cases).values_list("case__id", flat=True)
