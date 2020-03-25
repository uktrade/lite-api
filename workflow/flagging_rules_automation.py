from django.db.models import QuerySet

from applications.models import PartyOnApplication, GoodOnApplication
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
        from django.db import connection

        if flagging_rule.level == FlagLevels.CASE:
            print("CASE BEFORE: " + str(len(connection.queries)))
            open_cases = open_cases.filter(case_type__reference=flagging_rule.matching_value).values_list(
                "id", flat=True
            )

            flagging_rule.flag.cases.add(*open_cases)
            print("CASE AFTER: " + str(len(connection.queries)))
        elif flagging_rule.level == FlagLevels.GOOD:
            print("GOOD BEFORE: " + str(len(connection.queries)))

            good_in_query = GoodsQuery.objects.exclude(
                status__status__in=CaseStatusEnum.terminal_statuses() + [CaseStatusEnum.DRAFT]
            ).values_list("good_id", flat=True)
            flagging_rule.flag.goods.add(*good_in_query)

            good_types = GoodsType.objects.filter(application_id__in=open_cases).values_list("id", flat=True)
            flagging_rule.flag.goods_type.add(*good_types)

            goods = GoodOnApplication.objects.filter(application_id__in=open_cases).values_list("good_id", flat=True)
            flagging_rule.flag.goods.add(*goods)

            print("GOOD AFTER: " + str(len(connection.queries)))
        elif flagging_rule.level == FlagLevels.DESTINATION:
            print("DESTINATION BEFORE: " + str(len(connection.queries)))

            end_users = (
                EndUserAdvisoryQuery.objects.filter(end_user__country_id=flagging_rule.matching_value)
                .exclude(status__status__in=CaseStatusEnum.terminal_statuses() + [CaseStatusEnum.DRAFT])
                .values_list("end_user_id", flat=True)
            )
            flagging_rule.flag.parties.add(*end_users)

            non_eua_open_cases = open_cases.exclude(case_type_id=CaseTypeEnum.EUA.id).values_list("id", flat=True)

            parties = PartyOnApplication.objects.filter(
                application_id__in=non_eua_open_cases, party__country_id=flagging_rule.matching_value
            ).values_list("party_id", flat=True)
            flagging_rule.flag.parties.add(*parties)

            Country.objects.get(id=flagging_rule.matching_value).flags.add(flagging_rule.flag)
            print("DESTINATION AFTER: " + str(len(connection.queries)))


def apply_flagging_rule_for_flag(flag: Flag):
    """
    gets the flagging rules relating to a flag and applies them
    """
    flagging_rules = FlaggingRule.objects.filter(flag_id=flag.id)
    for rule in flagging_rules:
        apply_flagging_rule_to_all_open_cases(rule)
