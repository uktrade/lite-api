from django.urls import reverse

from api.cases.enums import AdviceLevel, AdviceType
from api.core.helpers import get_caseworker_frontend_url, get_exporter_frontend_url
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


def notify_caseworker_countersign_return(application):
    advice = (
        application.advice.filter(type=AdviceType.REFUSE, level=AdviceLevel.USER, countersigned_by__isnull=False)
        .order_by("-updated_at")
        .first()
    )
    relative_url = reverse("cases:countersign_advice", kwargs={"pk": application.id})
    data = {
        "case_reference": application.reference_code,
        "countersigner_name": f"{advice.countersigned_by.first_name} {advice.countersigned_by.last_name}",
        "countersign_comments": advice.countersign_comments,
        "recommendation_section_url": get_caseworker_frontend_url(relative_url),
    }
    email = advice.user.email
    _notify_caseworker_countersign_return(email, data)


def _notify_caseworker_countersign_return(email, data):
    payload = CaseWorkerCountersignCaseReturn(**data)
    send_email(email, TemplateType.CASEWORKER_COUNTERSIGN_CASE_RETURN, payload)
