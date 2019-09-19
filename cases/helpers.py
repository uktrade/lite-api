from collections import defaultdict

from cases.enums import AdviceType
from cases.libraries.activity_types import CaseActivityType
from cases.models import CaseActivity
from goods.models import Good
from goodstype.models import GoodsType
from parties.models import UltimateEndUser, EndUser, Consignee, ThirdParty
from static.countries.models import Country


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
            if advice.type == item.type \
                    and advice.text == item.text \
                    and advice.note == item.note \
                    and advice.proviso == item.proviso \
                    and [x for x in advice.denial_reasons.values_list()] == [x for x in item.denial_reasons.values_list()]:
                matches = True
            else:
                matches = False
        if matches is False:
            filtered_items.append(advice)

    return filtered_items


# pylint: disable = C901
def collate_advice(application_field, collection, case, user, advice_class):
    for key, value in collection:
        text = None
        note = None
        proviso = None
        denial_reasons = []
        type = None
        break_text = '\n-------\n'

        filtered_items = filter_out_duplicates(value)

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

            for denial_reason in advice.denial_reasons.values_list('id', flat=True):
                denial_reasons.append(denial_reason)

            if type:
                if type != advice.type:
                    type = AdviceType.CONFLICTING
            else:
                type = advice.type

        advice = advice_class(text=text,
                              case=case,
                              note=note,
                              proviso=proviso,
                              user=user,
                              type=type)

        # Set outside the constructor so it can apply only when necessary
        advice.team = user.team

        if application_field == 'good':
            advice.good = Good.objects.get(pk=key)
        elif application_field == 'end_user':
            advice.end_user = EndUser.objects.get(pk=key)
        elif application_field == 'country':
            advice.country = Country.objects.get(pk=key)
        elif application_field == 'ultimate_end_user':
            advice.ultimate_end_user = UltimateEndUser.objects.get(pk=key)
        elif application_field == 'goods_type':
            advice.goods_type = GoodsType.objects.get(pk=key)
        elif application_field == 'consignee':
            advice.consignee = Consignee.objects.get(pk=key)
        elif application_field == 'third_party':
            advice.third_party = ThirdParty.objects.get(pk=key)

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
        elif advice.country:
            countries[advice.country.id].append(advice)
        elif advice.ultimate_end_user:
            ultimate_end_users[advice.ultimate_end_user.id].append(advice)
        elif advice.goods_type:
            goods_types[advice.goods_type.id].append(advice)
        elif advice.consignee:
            consignees[advice.consignee.id].append(advice)
        elif advice.third_party:
            third_parties[advice.third_party.id].append(advice)

    collate_advice('end_user', end_users.items(), case, request.user, level)
    collate_advice('good', goods.items(), case, request.user, level)
    collate_advice('country', countries.items(), case, request.user, level)
    collate_advice('ultimate_end_user', ultimate_end_users.items(), case, request.user, level)
    collate_advice('goods_type', goods_types.items(), case, request.user, level)
    collate_advice('consignee', consignees.items(), case, request.user, level)
    collate_advice('third_party', third_parties.items(), case, request.user, level)


def create_advice_audit(case, user, level, action):
    CaseActivity.create(activity_type=CaseActivityType.ADVICE,
                        case=case,
                        user=user,
                        action=action,
                        level=level)
