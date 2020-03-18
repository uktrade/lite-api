from applications.models import PartyOnApplication
from cases.enums import CaseTypeEnum
from flags.enums import FlagLevels, FlagStatuses
from flags.models import FlaggingRule
from goods.models import Good
from goodstype.models import GoodsType
from parties.models import Party


def active_flagging_rules(level):
    return FlaggingRule.objects.prefetch_related("flag").filter(
        status=FlagStatuses.ACTIVE, flag__status=FlagStatuses.ACTIVE, level=level
    )


def apply_flagging_rules_to_case(object):
    apply_case_rules(object)
    apply_destination_rules_for_case(object)
    apply_good_flagging_rules_for_case(object)


def apply_case_rules(case):
    flags = list(
        active_flagging_rules(FlagLevels.CASE)
        .filter(matching_value=case.case_type.reference)
        .values_list("flag_id", flat=True)
    )

    if flags:
        case.flags.add(*flags)


def apply_destination_rules_for_case(case):
    flagging_rules = active_flagging_rules(FlagLevels.DESTINATION)

    if case.case_type.id == CaseTypeEnum.EUA.id:
        parties = [case.end_user]
    else:
        parties = Party.objects.filter(
            id__in=PartyOnApplication.objects.filter(application_id=case.id).values("party_id")
        )

    for party in parties:
        apply_destination_rule_on_party(party, flagging_rules)


def apply_destination_rule_on_party(party: Party, flagging_rules=None):
    if not flagging_rules:
        flagging_rules = active_flagging_rules(FlagLevels.DESTINATION)
    flags = list(flagging_rules.filter(matching_value=party.country.id).values_list("flag_id", flat=True))

    if flags:
        party.flags.add(*flags)


def apply_good_flagging_rules_for_case(case):
    flagging_rules = active_flagging_rules(FlagLevels.GOOD)
    if case.case_type.id == CaseTypeEnum.GOODS.id:
        goods = [case.good]
    elif case.case_type_id in [CaseTypeEnum.OICL.id, CaseTypeEnum.OGEL.id, CaseTypeEnum.OIEL.id, CaseTypeEnum.HMRC.id]:
        goods = GoodsType.objects.filter(application_id=case.id)
    else:
        goods = (
            Good.objects.prefetch_related("goods_on_application")
            .filter(goods_on_application__application_id=case.id)
            .distinct()
        )

    for good in goods:
        apply_goods_rules_for_good(good, flagging_rules)


def apply_goods_rules_for_good(good, flagging_rules=None):
    if not flagging_rules:
        flagging_rules = active_flagging_rules(FlagLevels.GOOD)
    flags = list(flagging_rules.filter(matching_value__iexact=good.control_code).values_list("flag_id", flat=True))

    if flags:
        good.flags.add(*flags)
