from applications.models import PartyOnApplication
from cases.models import Case
from flags.enums import FlagLevels, FlagStatuses
from flags.models import FlaggingRule
from goods.models import Good
from parties.models import Party


def active_flagging_rules(level):
    return FlaggingRule.objects.prefetch_related("flag").filter(
        status=FlagStatuses.ACTIVE, flag__status=FlagStatuses.ACTIVE, level=level
    )


def apply_rules_to_case(object):
    apply_case_rules(object)
    apply_destination_rules(object)
    apply_goods_rules_for_case(object)


def apply_case_rules(case: Case):
    flags = active_flagging_rules(FlagLevels.CASE).filter(matching_value=case.case_type.type).values_list("flag_id")
    case.flags.add(flags)
    case.flags.save()


def apply_destination_rules(case: Case):
    flagging_rules = active_flagging_rules(FlagLevels.DESTINATION)

    parties = Party.objects.filter(id__in=PartyOnApplication.objects.filter(application_id=case.id).values("party_id"))
    for party in parties:
        apply_destination_rule_on_party(party, flagging_rules)

    # CountryOnApplication ?


def apply_destination_rule_on_party(party: Party, flagging_rules=None):
    if not flagging_rules:
        flagging_rules = active_flagging_rules(FlagLevels.DESTINATION)
    flags = flagging_rules.filter(matching_value=party.country.id).values_list("flag_id")
    party.flags.add(flags)
    party.flags.save()


def apply_goods_rules_for_case(case: Case):
    flagging_rules = active_flagging_rules(FlagLevels.GOOD)
    goods = (
        Good.objects.prefetch_related("goods_on_application__application")
        .filter(goods_on_application__application_id=case.id)
        .distinct()
    )
    for good in goods:
        apply_goods_rules_for_good(good, flagging_rules)


def apply_goods_rules_for_good(good: Good, flagging_rules=None):
    if not flagging_rules:
        flagging_rules = active_flagging_rules(FlagLevels.GOOD)
    flags = flagging_rules.filter(matching_value__iexact=good.control_code).values_list("flag_id")

    good.flags.add(flags)
    good.flags.save()
