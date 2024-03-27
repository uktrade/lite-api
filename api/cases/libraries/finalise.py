from api.audit_trail.models import Audit
from api.cases.enums import AdviceType, CaseTypeSubTypeEnum, AdviceLevel
from api.cases.models import Advice, GoodCountryDecision
from api.applications.models import GoodOnApplication
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

    # If Open application, use GoodCountryDecision to override whether approve/refuse is needed.
    if case.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
        # Approve is only applicable if there is an approved GoodCountryDecision
        required_decisions.discard(AdviceType.APPROVE)
        decisions = GoodCountryDecision.objects.filter(case=case).values_list("approve", flat=True)
        if True in decisions:
            required_decisions.add(AdviceType.APPROVE)
        if False in decisions:
            required_decisions.add(AdviceType.REFUSE)

    return required_decisions


def remove_flags_on_finalisation(case):
    case_flags = case.flags.all()
    for flag in case_flags:
        if flag.remove_on_finalised:
            case.flags.remove(flag)
    case.save()


def remove_flags_from_audit_trail(case):
    flags_to_remove = Flag.objects.filter(remove_on_finalised=True)
    for flag in flags_to_remove:
        audit_logs = Audit.objects.filter(target_object_id=case.id, payload__icontains=flag.name)
        for audit_log in audit_logs:
            audit_log.delete()
