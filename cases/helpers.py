from collections import defaultdict

from cases.enums import AdviceType
from goods.models import Good
from parties.models import UltimateEndUser, Party, ThirdParty
from static.countries.models import Country
from users.models import GovUser, GovNotification


def filter_out_duplicates(advice_list):
    """
    This examines each piece of data in a set of advice for an object
    and if there are any exact duplicates it only returns one of them.
    """
    matches = False
    filtered_items = []
    for advice in advice_list:
        for item in filtered_items:
            # Compare each piece of unique advice against the new piece of advice being introduced
            if (
                advice.type == item.type
                and advice.text == item.text
                and advice.note == item.note
                and advice.proviso == item.proviso
                and [x for x in advice.denial_reasons.values_list()] == [x for x in item.denial_reasons.values_list()]
            ):
                matches = True
            else:
                matches = False
        if matches is False:
            filtered_items.append(advice)

    return filtered_items


def construct_coalesced_advice_values(
    filtered_items, text, note, proviso, denial_reasons, advice_type, case, advice_class, user,
):
    break_text = "\n-------\n"
    for advice in filtered_items:
        if text:
            text += break_text + advice.text
        else:
            text = advice.text

        if note:
            note += break_text + advice.note
        else:
            note = advice.note

        if advice.proviso:
            if proviso:
                proviso += break_text + advice.proviso
            else:
                proviso = advice.proviso

        for denial_reason in advice.denial_reasons.values_list("id", flat=True):
            denial_reasons.append(denial_reason)

        if advice_type:
            if advice_type != advice.type:
                advice_type = AdviceType.CONFLICTING
        else:
            advice_type = advice.type

    advice = advice_class(text=text, case=case, note=note, proviso=proviso, user=user, type=advice_type)

    return advice


def assign_field(application_field, advice, key):
    from goodstype.models import GoodsType

    if application_field == "good":
        advice.good = Good.objects.get(pk=key)
    elif application_field == "end_user":
        advice.end_user = Party.objects.get(pk=key)
    elif application_field == "country":
        advice.country = Country.objects.get(pk=key)
    elif application_field == "ultimate_end_user":
        advice.ultimate_end_user = UltimateEndUser.objects.get(pk=key)
    elif application_field == "goods_type":
        advice.goods_type = GoodsType.objects.get(pk=key)
    elif application_field == "consignee":
        advice.consignee = Party.objects.get(pk=key)
    elif application_field == "third_party":
        advice.third_party = ThirdParty.objects.get(pk=key)


def collate_advice(application_field, collection, case, user, advice_class):
    for key, value in collection:
        text = None
        note = None
        proviso = None
        denial_reasons = []
        advice_type = None

        filtered_items = filter_out_duplicates(value)

        advice = construct_coalesced_advice_values(
            filtered_items, text, note, proviso, denial_reasons, advice_type, case, advice_class, user,
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
            end_users[advice.end_user.id].append(advice)
        elif advice.country:
            countries[advice.country.id].append(advice)
        elif advice.good:
            goods[advice.good.id].append(advice)
        elif advice.ultimate_end_user:
            ultimate_end_users[advice.ultimate_end_user.id].append(advice)
        elif advice.goods_type:
            goods_types[advice.goods_type.id].append(advice)
        elif advice.consignee:
            consignees[advice.consignee.id].append(advice)
        elif advice.third_party:
            third_parties[advice.third_party.id].append(advice)

    collate_advice("end_user", end_users.items(), case, request.user, level)
    collate_advice("good", goods.items(), case, request.user, level)
    collate_advice("country", countries.items(), case, request.user, level)
    collate_advice("ultimate_end_user", ultimate_end_users.items(), case, request.user, level)
    collate_advice("goods_type", goods_types.items(), case, request.user, level)
    collate_advice("consignee", consignees.items(), case, request.user, level)
    collate_advice("third_party", third_parties.items(), case, request.user, level)


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
