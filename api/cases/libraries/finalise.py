from api.audit_trail.models import Audit
from api.applications.models import GoodOnApplication
from api.cases.enums import AdviceType, AdviceLevel
from api.cases.models import Advice
from api.flags.models import Flag


def get_required_decision_document_types(case):
    """
    Gets the list of required decision document types for advice
    """
    required_decisions = set(
        Advice.objects.filter(case=case, level=AdviceLevel.FINAL)
        .order_by("type")
        .distinct("type")
        .values_list("type", flat=True)
    )

    # Map Proviso -> Approve advice (Proviso results in Approve document)
    if AdviceType.PROVISO in required_decisions:
        required_decisions.add(AdviceType.APPROVE)
        required_decisions.remove(AdviceType.PROVISO)

    # Ensure that REFUSE advice requires an inform document
    if AdviceType.REFUSE in required_decisions:
        required_decisions.add(AdviceType.INFORM)

    # Check if no controlled good on application then no approval document required.
    has_controlled_good = GoodOnApplication.objects.filter(application=case.id, is_good_controlled=True).exists()

    if not has_controlled_good and AdviceType.NO_LICENCE_REQUIRED in required_decisions:
        required_decisions.discard(AdviceType.APPROVE)

    return required_decisions


def remove_flags_on_finalisation(case):
    flags_to_remove = Flag.objects.filter(remove_on_finalised=True)
    case.flags.remove(*flags_to_remove)


def remove_flags_from_audit_trail(case):
    flags_to_remove_ids = [str(flag.id) for flag in Flag.objects.filter(remove_on_finalised=True)]
    audit_logs = Audit.objects.filter(target_object_id=case.id)

    for flag_id in flags_to_remove_ids:
        for audit_log in audit_logs:
            payload = audit_log.payload
            if flag_id in payload.get("added_flags_id", []) or flag_id in payload.get("removed_flags_id", []):
                audit_log.delete()
