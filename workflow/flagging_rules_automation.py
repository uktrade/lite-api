from django.db.models import QuerySet

from applications.models import PartyOnApplication
from cases.enums import CaseTypeEnum
from cases.models import Case
from flags.enums import FlagLevels, FlagStatuses
from flags.models import FlaggingRule, Flag
from goods.models import Good
from goodstype.models import GoodsType
from parties.models import Party
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from queries.goods_query.models import GoodsQuery
from static.countries.models import Country
from static.statuses.enums import CaseStatusEnum


def get_active_flagging_rules_for_level(level):
    return FlaggingRule.objects.prefetch_related("flag").filter(
        status=FlagStatuses.ACTIVE, flag__status=FlagStatuses.ACTIVE, level=level
    )


def apply_flagging_rules_to_case(case):
    """
    Apply all active flagging rules to a case which meet the criteria
    """
    # flagging rules should only be applied to cases which are open
    if not (case.status.status == CaseStatusEnum.DRAFT or CaseStatusEnum.is_terminal(case.status.status)):
        apply_case_flagging_rules(case)
        apply_destination_flagging_rules_for_case(case)
        apply_good_flagging_rules_for_case(case)


def apply_case_flagging_rules(case):
    """
    Applies case type flagging rules to a case object
    """
    # get a list of flag_id's where the flagging rule matching value is equivalent to the case_type
    flags = (
        get_active_flagging_rules_for_level(FlagLevels.CASE)
        .filter(matching_value=case.case_type.reference)
        .values_list("flag_id", flat=True)
    )

    if flags:
        case.flags.add(*flags)


def apply_destination_flagging_rules_for_case(case, flagging_rule: QuerySet = None):
    """
    Applies destination type flagging rules to a case object
    """
    # If the flagging rules are specified then these is the only one we expect, else get all active
    flagging_rules = get_active_flagging_rules_for_level(FlagLevels.DESTINATION) if not flagging_rule else flagging_rule

    if case.case_type.id == CaseTypeEnum.EUA.id:
        # if the instance is not an EndUserAdvisoryQuery we need to get this to have access to the party
        if not isinstance(case, EndUserAdvisoryQuery):
            case = EndUserAdvisoryQuery.objects.get(pk=case.id)
        parties = [case.end_user]
    else:
        parties = Party.objects.filter(
            id__in=PartyOnApplication.objects.filter(application_id=case.id).values("party_id")
        )

    for party in parties:
        apply_destination_rule_on_party(party, flagging_rules)


def apply_destination_rule_on_party(party: Party, flagging_rules: QuerySet = None):
    # If the flagging rules are specified then these is the only one we expect, else get all active
    flagging_rules = (
        get_active_flagging_rules_for_level(FlagLevels.DESTINATION) if not flagging_rules else flagging_rules
    )

    # get a list of flag_id's where the flagging rule matching value is equivalent to the country id
    flags = flagging_rules.filter(matching_value=party.country.id).values_list("flag_id", flat=True)

    if flags:
        party.flags.add(*flags)


def apply_good_flagging_rules_for_case(case, flagging_rule: QuerySet = None):
    # If the flagging rules are specified then these is the only one we expect, else get all active
    flagging_rules = get_active_flagging_rules_for_level(FlagLevels.GOOD) if not flagging_rule else flagging_rule

    if case.case_type.id == CaseTypeEnum.GOODS.id:
        if not isinstance(case, GoodsQuery):
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


def apply_goods_rules_for_good(good, flagging_rules: QuerySet = None):
    # If the flagging rules are specified then these is the only one we expect, else get all active
    flagging_rules = get_active_flagging_rules_for_level(FlagLevels.GOOD) if not flagging_rules else flagging_rules

    # get a list of flag_id's where the flagging rule matching value is equivalent to the good control code
    flags = flagging_rules.filter(matching_value__iexact=good.control_code).values_list("flag_id", flat=True)

    if flags:
        good.flags.add(*flags)


def apply_flagging_rule_to_all_open_cases(flagging_rule: FlaggingRule):
    """
    Takes a flagging rule and applies it's flag on objects as relevant
    """
    if flagging_rule.status == FlagStatuses.ACTIVE and flagging_rule.flag.status == FlagStatuses.ACTIVE:
        open_cases = Case.objects.submitted().is_open()
        flagging_rule_queryset = FlaggingRule.objects.filter(id=flagging_rule.id)

        if flagging_rule.level == FlagLevels.CASE:
            open_cases = open_cases.filter(case_type__reference=flagging_rule.matching_value).all()
            for case in open_cases:
                case.flags.add(flagging_rule.flag)

        elif flagging_rule.level == FlagLevels.GOOD:
            for case in open_cases:
                apply_good_flagging_rules_for_case(case, flagging_rule_queryset)

        elif flagging_rule.level == FlagLevels.DESTINATION:
            for case in open_cases:
                apply_destination_flagging_rules_for_case(case, flagging_rule_queryset)

            Country.objects.get(id=flagging_rule.matching_value).flags.add(flagging_rule.flag)


def apply_flagging_rule_for_flag(flag: Flag):
    """
    gets the flagging rules relating to a flag and applies them
    """
    flagging_rules = FlaggingRule.objects.filter(flag_id=flag.id)
    for rule in flagging_rules:
        apply_flagging_rule_to_all_open_cases(rule)
