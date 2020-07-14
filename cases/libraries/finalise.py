from cases.enums import AdviceType, CaseTypeSubTypeEnum, AdviceLevel
from cases.models import Advice, GoodCountryDecision


def get_required_decision_document_types(case):
    """
    Gets the list of required decision document types for advice
    """
    required_decisions = set(
        Advice.objects.filter(case=case, level=AdviceLevel.FINAL).distinct("type").values_list("type", flat=True)
    )

    # Map Proviso -> Approve advice (Proviso results in Approve document)
    if AdviceType.PROVISO in required_decisions:
        required_decisions.add(AdviceType.APPROVE)
        required_decisions.remove(AdviceType.PROVISO)

    # If Open application, use GoodCountryDecision to override whether approve/refuse is needed.
    if case.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
        has_approval = GoodCountryDecision.objects.filter(case=case, approve=True).exists()
        if not has_approval:
            required_decisions.discard(AdviceType.APPROVE)

    return required_decisions
