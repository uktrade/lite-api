from django.db.models import QuerySet

from api.applications.models import PartyOnApplication, GoodOnApplication
from api.cases.enums import CaseTypeEnum
from api.cases.models import Case
from api.flags.enums import FlagLevels, FlagStatuses
from api.flags.models import FlaggingRule, Flag
from api.goods.enums import GoodStatus
from api.goods.models import Good
from api.goodstype.models import GoodsType
from api.parties.models import Party
from api.queries.end_user_advisories.models import EndUserAdvisoryQuery
from api.queries.goods_query.models import GoodsQuery
from api.static.countries.models import Country
from api.static.statuses.enums import CaseStatusEnum


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
    ratings = good.control_list_entries.values_list("rating", flat=True)
    flagging_rules = flagging_rules.filter(matching_value__in=ratings)

    if isinstance(good, Good) and good.status != GoodStatus.VERIFIED:
        flagging_rules = flagging_rules.exclude(is_for_verified_goods_only=True)

    flags = flagging_rules.values_list("flag_id", flat=True)

    if flags:
        good.flags.add(*flags)


def apply_flagging_rule_to_all_open_cases(flagging_rule: FlaggingRule):
    """
    Takes a flagging rule and creates a relationship between it's flag and objects that meet match conditions
    """
    if flagging_rule.status == FlagStatuses.ACTIVE and flagging_rule.flag.status == FlagStatuses.ACTIVE:
        # Flagging rules should only be applied to open cases
        draft_and_terminal_statuses = [CaseStatusEnum.DRAFT, *CaseStatusEnum.terminal_statuses()]
        open_cases = Case.objects.exclude(status__status__in=draft_and_terminal_statuses)

        # Apply the flagging rule to different entities depending on the rule's level
        if flagging_rule.level == FlagLevels.CASE:
            # Add flag to all open Cases
            open_cases = open_api.cases.filter(case_type__reference=flagging_rule.matching_value).values_list(
                "id", flat=True
            )

            flagging_rule.flag.api.cases.add(*open_cases)

        elif flagging_rule.level == FlagLevels.GOOD:
            # Add flag to all Goods on open Goods Queries
            goods_in_query = GoodsQuery.objects.filter(
                good__control_list_entries__rating__in=[flagging_rule.matching_value]
            ).exclude(status__status__in=draft_and_terminal_statuses)

            if flagging_rule.is_for_verified_goods_only:
                goods_in_query = goods_in_query.filter(good__status=GoodStatus.VERIFIED)

            goods_in_query = goods_in_query.values_list("good_id", flat=True)
            flagging_rule.flag.goods.add(*goods_in_query)

            # Add flag to all Goods Types
            goods_types = GoodsType.objects.filter(
                application_id__in=open_cases, control_list_entries__rating__in=[flagging_rule.matching_value]
            ).values_list("id", flat=True)
            flagging_rule.flag.goods_type.add(*goods_types)

            # Add flag to all open Applications
            goods = GoodOnApplication.objects.filter(
                application_id__in=open_cases, good__control_list_entries__rating__in=[flagging_rule.matching_value]
            )

            if flagging_rule.is_for_verified_goods_only:
                goods = goods.filter(good__status=GoodStatus.VERIFIED)

            goods = goods.values_list("good_id", flat=True)
            flagging_rule.flag.goods.add(*goods)

        elif flagging_rule.level == FlagLevels.DESTINATION:
            # Add flag to all End Users on open End User Advisory Queries
            end_users = (
                EndUserAdvisoryQuery.objects.filter(end_user__country_id=flagging_rule.matching_value)
                .exclude(status__status__in=draft_and_terminal_statuses)
                .values_list("end_user_id", flat=True)
            )
            flagging_rule.flag.parties.add(*end_users)

            # Add flag to all Parties on open Applications
            parties = PartyOnApplication.objects.filter(
                application_id__in=open_cases, party__country_id=flagging_rule.matching_value
            ).values_list("party_id", flat=True)
            flagging_rule.flag.parties.add(*parties)

            Country.objects.get(id=flagging_rule.matching_value).flags.add(flagging_rule.flag)


def apply_flagging_rule_for_flag(flag: Flag):
    """
    gets the flagging rules relating to a flag and applies them
    """
    flagging_rules = FlaggingRule.objects.filter(flag=flag)
    for rule in flagging_rules:
        apply_flagging_rule_to_all_open_cases(rule)
