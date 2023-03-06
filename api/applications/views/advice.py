from django.conf import settings

from api.cases.enums import AdviceLevel, AdviceType
from api.cases.models import CountersignAdvice
from api.flags.models import Flag
from api.flags.enums import FlagStatuses
from api.teams.models import Team

from lite_routing.routing_rules_internal.enums import FlagsEnum


class MissingCounterSignature(Exception):
    pass


def get_lu_countersigning_flag_names():
    return Flag.objects.filter(
        id__in=[
            FlagsEnum.LU_COUNTER_REQUIRED,
            FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED,
            FlagsEnum.MANPADS,
            FlagsEnum.AP_LANDMINE,
        ],
        status=FlagStatuses.ACTIVE,
    ).values_list("name", flat=True)


def get_lu_sr_mgr_countersigning_flag_names():
    return Flag.objects.filter(
        id__in=[
            FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED,
            FlagsEnum.MANPADS,
        ],
        status=FlagStatuses.ACTIVE,
    ).values_list("name", flat=True)


def validate_lu_countersignatures(application, countersign_flags):
    if not settings.FEATURE_COUNTERSIGN_ROUTING_ENABLED:
        return True

    # We are here means this application needs countersigning so check
    # if countersignatures of all orders are present and accepted
    case = application.get_case()
    lu_team = Team.objects.get(id="58e77e47-42c8-499f-a58d-94f94541f8c6")
    sr_lu_mgr_countersign_flags = get_lu_sr_mgr_countersigning_flag_names()

    countersign_orders = [1]
    if countersign_flags.intersection(sr_lu_mgr_countersign_flags):
        countersign_orders.append(2)

    countersign_advice = CountersignAdvice.objects.filter(
        order__in=countersign_orders,
        case=case,
        advice__team=lu_team,
        advice__level=AdviceLevel.FINAL,
        advice__type__in=[AdviceType.APPROVE, AdviceType.PROVISO],
    )

    return countersign_advice and all(advice.outcome_accepted for advice in countersign_advice)
