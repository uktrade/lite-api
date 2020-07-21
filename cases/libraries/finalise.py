from cases.enums import AdviceType, CaseTypeSubTypeEnum, AdviceLevel
from cases.models import Advice, GoodCountryDecision


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
