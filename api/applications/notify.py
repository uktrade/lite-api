from django.urls import reverse

from api.cases.enums import AdviceLevel, AdviceType, CountersignOrder
from api.cases.models import CountersignAdvice
from api.core.helpers import get_caseworker_frontend_url, get_exporter_frontend_url
from api.staticdata.statuses.enums import CaseStatusEnum
from api.teams.enums import TeamIdEnum
from api.teams.models import Team
from gov_notify.enums import TemplateType
from gov_notify.payloads import CaseWorkerCountersignCaseReturn, ExporterCaseOpenedForEditing
from gov_notify.service import send_email


def _notify_exporter_case_opened_for_editing(email, data):
    payload = ExporterCaseOpenedForEditing(**data)
    send_email(
        email,
        TemplateType.EXPORTER_CASE_OPENED_FOR_EDITING,
        payload,
    )


def notify_exporter_case_opened_for_editing(application):
    exporter = application.submitted_by
    _notify_exporter_case_opened_for_editing(
        exporter.email,
        {
            "user_first_name": exporter.first_name,
            "application_reference": application.reference_code,
            "exporter_frontend_url": get_exporter_frontend_url("/"),
        },
    )


# def notify_caseworker_countersign_return(user_email, application, countersign_advice):
def notify_caseworker_countersign_return(case):
    countersign_order = (
        CountersignOrder.FIRST_COUNTERSIGN
        if case._previous_status.status == CaseStatusEnum.FINAL_REVIEW_COUNTERSIGN
        else CountersignOrder.SECOND_COUNTERSIGN
    )
    countersign_advice = CountersignAdvice.objects.get(
        case=case,
        valid=True,
        order=countersign_order,
        outcome_accepted=False,
        advice__user__team=Team.objects.get(id=TeamIdEnum.LICENSING_UNIT),
        advice__level=AdviceLevel.FINAL,
        advice__type=AdviceType.REFUSE,
    )
    relative_url = reverse("cases:countersign_decision_advice", kwargs={"pk": case.id})
    countersigner = countersign_advice.countersigned_user
    data = {
        "case_reference": case.reference_code,
        "countersigned_user_name": f"{countersigner.first_name} {countersigner.last_name}",
        "countersign_reasons": countersign_advice.reasons,
        "recommendation_section_url": get_caseworker_frontend_url(relative_url),
    }
    _notify_caseworker_countersign_return(case.case_officer.email, data)


def _notify_caseworker_countersign_return(email, data):
    payload = CaseWorkerCountersignCaseReturn(**data)
    send_email(email, TemplateType.CASEWORKER_COUNTERSIGN_CASE_RETURN, payload)
