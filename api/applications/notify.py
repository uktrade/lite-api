from api.core.helpers import get_exporter_frontend_url
from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterCaseOpenedForEditing
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
