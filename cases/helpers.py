from collections import defaultdict

import reversion

from cases.enums import AdviceType
from end_user.models import EndUser
from goods.models import Good
from goodstype.models import GoodsType
from static.countries.models import Country


def collate_advice(application_field, collection, case, user, advice_class):
    for key, value in collection:
        text = None
        note = None
        proviso = None
        denial_reasons = []
        type = None

        for advice in value:
            if text:
                text += '\n-------\n' + advice.text
            else:
                text = advice.text

            if note:
                note += '\n-------\n' + advice.note
            else:
                note = advice.note

            if advice.proviso:
                if proviso:
                    proviso += '\n-------\n' + advice.proviso
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
            advice.ultimate_end_user = EndUser.objects.get(pk=key)
        elif application_field == 'goods_type':
            advice.goods_type = GoodsType.objects.get(pk=key)

        advice.save()
        advice.denial_reasons.set(denial_reasons)


def create_grouped_advice(case, request, advice, level):
    end_users = defaultdict(list)
    ultimate_end_users = defaultdict(list)
    goods = defaultdict(list)
    goods_types = defaultdict(list)
    countries = defaultdict(list)

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
            ultimate_end_users[advice.coutnry.id].append(advice)
        elif advice.goods_type:
            goods_types[advice.coutnry.id].append(advice)

    collate_advice('end_user', end_users.items(), case, request.user, level)
    collate_advice('good', goods.items(), case, request.user, level)
    collate_advice('country', countries.items(), case, request.user, level)
    collate_advice('ultimate_end_user', ultimate_end_users.items(), case, request.user, level)
    collate_advice('goods_type', goods_types.items(), case, request.user, level)


# TODO: update audit trail message to fit with standards and how it will be displayed on the frontend
def create_advice_audit(case, user, level, action):
    with reversion.create_revision():
        reversion.set_comment(
            ('{"advice": "' + action + ' ' + level + ' ' + 'advice"}')
        )
        reversion.set_user(user)

        # We call save on the case with no changes in order to create our audit comment attached to the
        # case, not to any individual piece of advice
        case.save()
