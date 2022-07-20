from api.core.helpers import get_exporter_frontend_url
from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterLicenceIssued
from gov_notify.service import send_email


def _notify_exporter_licence_issued(email, data):
    payload = ExporterLicenceIssued(**data)
    send_email(
        email,
        TemplateType.EXPORTER_LICENCE_ISSUED,
        payload,
    )


def notify_exporter_licence_issued(licence):
    exporter = licence.case.submitted_by
    case = licence.case.get_case()
    _notify_exporter_licence_issued(
        exporter.email,
        {
            "user_first_name": exporter.first_name,
            "application_reference": case.reference_code,
            "exporter_frontend_url": get_exporter_frontend_url("/"),
        },
    )
