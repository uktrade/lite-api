from django.db.models import F

from api.core.helpers import get_exporter_frontend_url
from api.cases.models import Case
from gov_notify.enums import TemplateType
from gov_notify.payloads import (
    ExporterECJUQuery,
    ExporterLicenceIssued,
    ExporterLicenceRefused,
    ExporterNoLicenceRequired,
    ExporterLicenceRevoked,
    ExporterInformLetter,
)
from gov_notify.service import send_email


def _notify_exporter_licence_issued(email, data):
    payload = ExporterLicenceIssued(**data)
    send_email(
        email,
        TemplateType.EXPORTER_LICENCE_ISSUED,
        payload,
    )


def notify_exporter_licence_issued(case):
    exporter = case.submitted_by
    case = case.get_case()
    _notify_exporter_licence_issued(
        exporter.email,
        {
            "user_first_name": exporter.first_name,
            "application_reference": case.reference_code,
            "exporter_frontend_url": get_exporter_frontend_url("/"),
        },
    )


def _notify_exporter_licence_refused(email, data):
    payload = ExporterLicenceRefused(**data)
    send_email(
        email,
        TemplateType.EXPORTER_LICENCE_REFUSED,
        payload,
    )


def notify_exporter_licence_refused(case):
    exporter = case.submitted_by
    case = case.get_case()
    _notify_exporter_licence_refused(
        exporter.email,
        {
            "user_first_name": exporter.first_name,
            "application_reference": case.reference_code,
            "exporter_frontend_url": get_exporter_frontend_url("/"),
        },
    )


def _notify_exporter_licence_revoked(email, data):
    payload = ExporterLicenceRevoked(**data)
    send_email(
        email,
        TemplateType.EXPORTER_LICENCE_REVOKED,
        payload,
    )


def notify_exporter_licence_revoked(licence):
    exporter = licence.case.submitted_by
    case = licence.case.get_case()
    _notify_exporter_licence_revoked(
        exporter.email,
        {
            "user_first_name": exporter.first_name,
            "application_reference": case.reference_code,
            "exporter_frontend_url": get_exporter_frontend_url("/"),
        },
    )


def notify_exporter_ecju_query(case_pk):
    case_info = (
        Case.objects.annotate(
            email=F("submitted_by__baseuser_ptr__email"), first_name=F("submitted_by__baseuser_ptr__first_name")
        )
        .values("id", "email", "first_name", "reference_code")
        .get(id=case_pk)
    )

    # This deliberately avoids using a more specific URL since there are a few possible here,
    # so the likelihood of them changing in the exporter app is higher
    exporter_frontend_url = get_exporter_frontend_url("/")

    _notify_exporter_ecju_query(
        case_info["email"],
        {
            "exporter_first_name": case_info["first_name"] or "",
            "case_reference": case_info["reference_code"],
            "exporter_frontend_url": exporter_frontend_url,
        },
    )


def _notify_exporter_ecju_query(email, data):
    payload = ExporterECJUQuery(**data)
    send_email(email, TemplateType.EXPORTER_ECJU_QUERY, payload)


def _notify_exporter_no_licence_required(email, data):
    payload = ExporterNoLicenceRequired(**data)
    send_email(email, TemplateType.EXPORTER_NO_LICENCE_REQUIRED, payload)


def notify_exporter_no_licence_required(case):
    exporter = case.submitted_by
    case = case.get_case()
    _notify_exporter_no_licence_required(
        exporter.email,
        {
            "user_first_name": exporter.first_name,
            "application_reference": case.reference_code,
            "exporter_frontend_url": get_exporter_frontend_url("/"),
        },
    )


def notify_exporter_inform_letter(case):
    case = case.get_case()
    exporter = case.submitted_by
    payload = ExporterInformLetter(
        user_first_name=exporter.first_name,
        application_reference=case.reference_code,
        exporter_frontend_url=get_exporter_frontend_url("/"),
    )
    send_email(exporter.email, TemplateType.EXPORTER_INFORM_LETTER, payload)
