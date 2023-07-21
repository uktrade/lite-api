from django.db.models import Q, QuerySet

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
from api.staticdata.countries.models import Country
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.control_list_entries.helpers import get_clc_child_nodes, get_clc_parent_nodes

from lite_routing.routing_rules_internal.flagging_rules_criteria import (
    run_flagging_rules_criteria_case,
    run_flagging_rules_criteria_product,
    run_flagging_rules_criteria_destination,
)


def _apply_python_flagging_rules(level, object):
    flags = []

    for rule in FlaggingRule.objects.filter(level=level, status=FlagStatuses.ACTIVE, is_python_criteria=True):
        rule_applies = False
        if level == FlagLevels.CASE:
            rule_applies = run_flagging_rules_criteria_case(rule.id, object)
        elif level == FlagLevels.GOOD:
            rule_applies = run_flagging_rules_criteria_product(rule.id, object)
        elif level == FlagLevels.DESTINATION:
            rule_applies = run_flagging_rules_criteria_destination(rule.id, object)

        if rule_applies:
            flags.append(rule.flag_id)

    return flags


def get_active_legacy_flagging_rules_for_level(level):
    return FlaggingRule.objects.prefetch_related("flag").filter(
        status=FlagStatuses.ACTIVE, flag__status=FlagStatuses.ACTIVE, level=level, is_python_criteria=False
    )


def apply_flagging_rules_to_case(case):
    """
    Apply all active flagging rules to a case which meet the criteria
    """
    # flagging rules should only be applied to cases which are open
    if case.status.status == CaseStatusEnum.DRAFT or CaseStatusEnum.is_terminal(case.status.status):
        return

    apply_case_flagging_rules(case)
    apply_destination_flagging_rules_for_case(case)
    apply_good_flagging_rules_for_case(case)


def apply_case_flagging_rules(case):
    """
    Applies case type flagging rules to a case object
    """
    # get a list of flag_id's where the flagging rule matching value is equivalent to the case_type
    flags = (
        get_active_legacy_flagging_rules_for_level(FlagLevels.CASE)
        .filter(matching_values__overlap=[case.case_type.reference])
        .values_list("flag_id", flat=True)
    )

    flags = list(flags)
    flags.extend(_apply_python_flagging_rules(FlagLevels.CASE, case))

    if flags:
        case.flags.add(*flags)


def apply_destination_flagging_rules_for_case(case, flagging_rule: QuerySet = None):
    """
    Applies destination type flagging rules to a case object
    """
    # If the flagging rules are specified then these is the only one we expect, else get all active
    flagging_rules = (
        get_active_legacy_flagging_rules_for_level(FlagLevels.DESTINATION) if not flagging_rule else flagging_rule
    )

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
        get_active_legacy_flagging_rules_for_level(FlagLevels.DESTINATION) if not flagging_rules else flagging_rules
    )

    # get a list of flag_id's where the flagging rule matching value is equivalent to the country id
    flags = flagging_rules.filter(matching_values__overlap=[party.country.id]).values_list("flag_id", flat=True)

    flags = list(flags)
    flags.extend(_apply_python_flagging_rules(FlagLevels.DESTINATION, party))

    if flags:
        party.flags.add(*flags)


def apply_good_flagging_rules_for_case(case, flagging_rule: QuerySet = None):
    # If the flagging rules are specified then these is the only one we expect, else get all active
    flagging_rules = get_active_legacy_flagging_rules_for_level(FlagLevels.GOOD) if not flagging_rule else flagging_rule

    if case.case_type_id in [CaseTypeEnum.OICL.id, CaseTypeEnum.OGEL.id, CaseTypeEnum.OIEL.id, CaseTypeEnum.HMRC.id]:
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
    flagging_rules = (
        get_active_legacy_flagging_rules_for_level(FlagLevels.GOOD) if not flagging_rules else flagging_rules
    )

    # get a list of flag_id's where the flagging rule matching value is equivalent to the good control code
    ratings = [r for r in good.control_list_entries.values_list("rating", flat=True)]
    group_ratings = []
    for rating in ratings:
        group_ratings.extend(get_clc_parent_nodes(rating))

    flagging_rules = flagging_rules.filter(
        Q(matching_values__overlap=ratings) | Q(matching_groups__overlap=group_ratings)
    ).exclude(excluded_values__overlap=(ratings + group_ratings))

    if isinstance(good, Good) and good.status != GoodStatus.VERIFIED:
        flagging_rules = flagging_rules.exclude(is_for_verified_goods_only=True)

    flags = flagging_rules.values_list("flag_id", flat=True)

    flags = list(flags)
    flags.extend(_apply_python_flagging_rules(FlagLevels.GOOD, good))

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
            open_cases = open_cases.filter(case_type__reference__in=flagging_rule.matching_values).values_list(
                "id", flat=True
            )

            flagging_rule.flag.cases.add(*open_cases)

        elif flagging_rule.level == FlagLevels.GOOD:
            clc_entries_of_groups = []
            for group in flagging_rule.matching_groups:
                child_entries = get_clc_child_nodes(group)
                clc_entries_of_groups.extend(child_entries)

            matching_values = flagging_rule.matching_values + clc_entries_of_groups

            # excluded_values contain individual entries and groups
            excluded_values = []
            for rating in flagging_rule.excluded_values:
                entries = get_clc_child_nodes(rating)
                excluded_values.extend(entries)

            # Add flag to all Goods Types
            goods_types = GoodsType.objects.filter(
                application_id__in=open_cases, control_list_entries__rating__in=matching_values
            )

            if excluded_values:
                goods_types = goods_types.exclude(
                    application_id__in=open_cases, control_list_entries__rating__in=excluded_values
                )

            goods_types = goods_types.values_list("id", flat=True)

            flagging_rule.flag.goods_type.add(*goods_types)

            # Add flag to all open Applications
            goods = GoodOnApplication.objects.filter(
                application_id__in=open_cases, good__control_list_entries__rating__in=matching_values
            )

            if excluded_values:
                goods = goods.exclude(
                    application_id__in=open_cases, good__control_list_entries__rating__in=excluded_values
                )

            if flagging_rule.is_for_verified_goods_only:
                goods = goods.filter(good__status=GoodStatus.VERIFIED)

            goods = goods.values_list("good_id", flat=True)
            flagging_rule.flag.goods.add(*goods)

        elif flagging_rule.level == FlagLevels.DESTINATION:
            # Add flag to all End Users on open End User Advisory Queries
            end_users = (
                EndUserAdvisoryQuery.objects.filter(end_user__country_id__in=flagging_rule.matching_values)
                .exclude(status__status__in=draft_and_terminal_statuses)
                .values_list("end_user_id", flat=True)
            )
            flagging_rule.flag.parties.add(*end_users)

            # Add flag to all Parties on open Applications
            parties = PartyOnApplication.objects.filter(
                application_id__in=open_cases, party__country_id__in=flagging_rule.matching_values
            ).values_list("party_id", flat=True)
            flagging_rule.flag.parties.add(*parties)

            countries = Country.objects.filter(id__in=flagging_rule.matching_values).values_list("id", flat=True)
            flagging_rule.flag.countries.add(*countries)


def apply_flagging_rule_for_flag(flag: Flag):
    """
    gets the flagging rules relating to a flag and applies them
    """
    flagging_rules = FlaggingRule.objects.filter(flag=flag)
    for rule in flagging_rules:
        apply_flagging_rule_to_all_open_cases(rule)
