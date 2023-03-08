from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.cases.enums import AdviceLevel, AdviceType, CountersignOrder
from api.cases.models import CountersignAdvice
from api.flags.models import Flag
from api.flags.enums import FlagStatuses
from api.teams.models import Team

from lite_routing.routing_rules_internal.enums import FlagsEnum


class CounterSignatureIncompleteError(Exception):
    """
    Exception raised if we countersignatures are incomplete
     - When required countersignatures are missing
     - When required countersignatures are present but if atleast one of them is rejected
    """

    pass


class CountersignInvalidAdviceTypeError(Exception):
    """
    Exception raised if we encounter invalid Advice types for countersigning, eg REFUSE type
    """

    pass


def lu_countersigning_flags_all():
    return Flag.objects.filter(
        id__in=[
            FlagsEnum.LU_COUNTER_REQUIRED,
            FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED,
            FlagsEnum.MANPADS,
            FlagsEnum.AP_LANDMINE,
        ],
        status=FlagStatuses.ACTIVE,
    )


def lu_sr_mgr_countersigning_flags():
    return Flag.objects.filter(
        id__in=[
            FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED,
            FlagsEnum.MANPADS,
        ],
        status=FlagStatuses.ACTIVE,
    )


def ensure_lu_countersign_complete(application):
    """
    If a Case requires LU countersigning then it ensure necessary countersignatures
    are present and approved.

    Certain cases need double countersigning so it checks for countersignatures
    of both orders (FIRST_COUNTERSIGN, SECOND_COUNTERSIGN) where applicable.

    Once the countersignatures are valid then it removes the flags that blocks
    finalising the Case.
    """
    case = application.get_case()
    lu_team = Team.objects.get(id="58e77e47-42c8-499f-a58d-94f94541f8c6")

    all_case_flags = {item for item in case.parameter_set() if isinstance(item, Flag)}
    countersign_flags = all_case_flags.intersection(lu_countersigning_flags_all())
    if not countersign_flags:
        return

    # We are here means atleast first countersign is required so
    # check if second countersign is also required
    countersign_orders = [CountersignOrder.FIRST_COUNTERSIGN]
    lu_sr_mgr_countersign_required = countersign_flags.intersection(lu_sr_mgr_countersigning_flags())
    if lu_sr_mgr_countersign_required:
        countersign_orders = [CountersignOrder.FIRST_COUNTERSIGN, CountersignOrder.SECOND_COUNTERSIGN]

    # If a Case is being refused then it won't reach countersigning queues but
    # if it is routed unexpectedly then we need to catch and raise error
    refused_countersign_advice = CountersignAdvice.objects.filter(
        order__in=countersign_orders,
        case=case,
        advice__team=lu_team,
        advice__level=AdviceLevel.FINAL,
        advice__type=AdviceType.REFUSE,
    )
    if refused_countersign_advice.exists():
        raise CountersignInvalidAdviceTypeError(
            "This application cannot be finalised as the countersigning has been refused"
        )

    # check countersignatures for the required orders
    for order in countersign_orders:
        countersign_advice = CountersignAdvice.objects.filter(
            order=order,
            case=case,
            advice__team=lu_team,
            advice__level=AdviceLevel.FINAL,
            advice__type__in=[AdviceType.APPROVE, AdviceType.PROVISO],
        )
        if not (countersign_advice and all(advice.outcome_accepted for advice in countersign_advice)):
            raise CounterSignatureIncompleteError(
                "This applications requires countersigning and the required countersignatures are not completed"
            )

    # Remove countersigning flags that block finalising
    # MANPADS and AP_LANDMINE are also countersigning flags but they are related
    # to product attributes and we want to retain them, they also don't
    # block finalising the case but if they are applied then we need to ensure
    # necessary countersignatures are present before finalising the Case
    countersign_process_flags = Flag.objects.filter(
        id__in=[
            FlagsEnum.LU_COUNTER_REQUIRED,
            FlagsEnum.LU_SENIOR_MANAGER_CHECK_REQUIRED,
        ],
        status=FlagStatuses.ACTIVE,
    )
    flags_to_remove = countersign_flags.intersection(countersign_process_flags)
    for party_on_application in application.parties.all():
        party_on_application.party.flags.remove(*flags_to_remove)
        audit_trail_service.create_system_user_audit(
            verb=AuditType.DESTINATION_REMOVE_FLAGS,
            action_object=party_on_application.party,
            target=case,
            payload={
                "removed_flags": [flag.name for flag in flags_to_remove],
                "destination_name": party_on_application.party.name,
                "additional_text": "Removing flags as required countersignatures present and approved",
            },
        )
