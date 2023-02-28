from django.urls import reverse

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


def notify_caseworker_countersign_return(user_email, application, countersign_advice):
    relative_url = reverse("cases:countersign_advice", kwargs={"pk": application.id})
    countersigner = countersign_advice.countersigned_user
    data = {
        "case_reference": application.reference_code,
        "countersigned_user_name": f"{countersigner.first_name} {countersigner.last_name}",
        "countersign_reasons": countersign_advice.reasons,
        "recommendation_section_url": get_caseworker_frontend_url(relative_url),
    }
    _notify_caseworker_countersign_return(user_email, data)


def _notify_caseworker_countersign_return(email, data):
    payload = CaseWorkerCountersignCaseReturn(**data)
    send_email(email, TemplateType.CASEWORKER_COUNTERSIGN_CASE_RETURN, payload)
