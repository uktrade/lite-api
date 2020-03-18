from applications.models import PartyOnApplication
from cases.enums import CaseTypeEnum
from cases.models import Case
from flags.enums import FlagLevels, FlagStatuses
from flags.models import FlaggingRule
from goods.models import Good
from goodstype.models import GoodsType
from parties.models import Party
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from queries.goods_query.models import GoodsQuery
from static.countries.models import Country


def active_flagging_rules_for_level(level):
    return FlaggingRule.objects.prefetch_related("flag").filter(
        status=FlagStatuses.ACTIVE, flag__status=FlagStatuses.ACTIVE, level=level
    )


def apply_flagging_rules_to_case(object):
    apply_case_rules(object)
    apply_destination_rules_for_case(object)
    apply_good_flagging_rules_for_case(object)


def apply_case_rules(case):
    flags = list(
        active_flagging_rules_for_level(FlagLevels.CASE)
        .filter(matching_value=case.case_type.reference)
        .values_list("flag_id", flat=True)
    )

    if flags:
        case.flags.add(*flags)


def apply_destination_rules_for_case(case, flagging_rule=None):
    flagging_rules = active_flagging_rules_for_level(FlagLevels.DESTINATION) if not flagging_rule else flagging_rule

    if case.case_type.id == CaseTypeEnum.EUA.id:
        if isinstance(case, Case):
            case = EndUserAdvisoryQuery.objects.get(pk=case.id)
        parties = [case.end_user]
    else:
        parties = Party.objects.filter(
            id__in=PartyOnApplication.objects.filter(application_id=case.id).values("party_id")
        )

    for party in parties:
        apply_destination_rule_on_party(party, flagging_rules)


def apply_destination_rule_on_party(party: Party, flagging_rules=None):
    if not flagging_rules:
        flagging_rules = active_flagging_rules_for_level(FlagLevels.DESTINATION)
    flags = list(flagging_rules.filter(matching_value=party.country.id).values_list("flag_id", flat=True))

    if flags:
        party.flags.add(*flags)


def apply_good_flagging_rules_for_case(case, flagging_rule=None):
    flagging_rules = active_flagging_rules_for_level(FlagLevels.GOOD) if not flagging_rule else flagging_rule
    if case.case_type.id == CaseTypeEnum.GOODS.id:
        if isinstance(case, Case):
            case = GoodsQuery.objects.get(pk=case.id)
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
        flagging_rules = active_flagging_rules_for_level(FlagLevels.GOOD)
    flags = list(flagging_rules.filter(matching_value__iexact=good.control_code).values_list("flag_id", flat=True))

    if flags:
        good.flags.add(*flags)


def apply_flagging_rule_to_all_open_cases(flagging_rule):
    if flagging_rule.status == FlagStatuses.ACTIVE and flagging_rule.flag.status == FlagStatuses.ACTIVE:
        open_cases = Case.objects.submitted().is_open()
        flagging_rule_queryset = FlaggingRule.objects.filter(id=flagging_rule.id)

        if flagging_rule.level == FlagLevels.CASE:
            open_cases.filter(case_type__reference=flagging_rule.matching_value).all()
            for case in open_cases:
                case.flags.add(flagging_rule.flag)

        elif flagging_rule.level == FlagLevels.GOOD:
            for case in open_cases:
                apply_good_flagging_rules_for_case(case, flagging_rule_queryset)

        elif flagging_rule.level == FlagLevels.DESTINATION:
            for case in open_cases:
                apply_destination_rules_for_case(case, flagging_rule_queryset)

                Country.objects.get(id=flagging_rule.matching_value).flags.add(flagging_rule.flag)
