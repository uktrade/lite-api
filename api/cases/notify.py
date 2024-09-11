from django.db.models import F

from api.core.helpers import get_exporter_frontend_url
from api.cases.models import Case, EcjuQuery
from gov_notify.registry import notify_email
from gov_notify.enums import TemplateType
from gov_notify.payloads import (
    ExporterECJUQuery,
    ExporterECJUQueryChaser,
    ExporterNoLicenceRequired,
    ExporterInformLetter,
    ExporterAppealAcknowledgement,
    ExporterLicenceSuspended,
)
from gov_notify.service import send_email


def notify_exporter_licence_payload(case):
    exporter = case.submitted_by
    case = case.get_case()

    return notify_email.Payload(
        recipient_email=exporter.email,
        payload={
            "user_first_name": exporter.first_name,
            "application_reference": case.reference_code,
            "exporter_frontend_url": get_exporter_frontend_url("/"),
        },
    )


@notify_email.register(template_id="f2757d61-2319-4279-82b2-a52170b0222a")
def notify_exporter_licence_issued(case):
    return notify_exporter_licence_payload(case)


@notify_email.register(template_id="6d8089be-9551-456d-8305-d4185555f725")
def notify_exporter_licence_refused(case):
    return notify_exporter_licence_payload(case)


@notify_email.register(template_id="05cec19b-2e65-480d-b859-7116aa5c2e44")
def notify_exporter_licence_revoked(licence):
    exporter = licence.case.submitted_by
    case = licence.case.get_case()

    return notify_email.Payload(
        recipient_email=exporter.email,
        payload={
            "user_first_name": exporter.first_name,
            "application_reference": case.reference_code,
        },
    )


def _notify_exporter_licence_suspended(email, data):
    payload = ExporterLicenceSuspended(**data)
    send_email(
        email,
        TemplateType.EXPORTER_LICENCE_SUSPENDED,
        payload,
    )


def notify_exporter_licence_suspended(licence):
    exporter = licence.case.submitted_by
    _notify_exporter_licence_suspended(
        exporter.email,
        {
            "user_first_name": exporter.first_name,
            "licence_reference": licence.reference_code,
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


def notify_exporter_ecju_query_chaser(ecju_query_id, callback):
    ecju_query = EcjuQuery.objects.get(id=ecju_query_id)

    exporter_frontend_ecju_queries_url = get_exporter_frontend_url(f"/applications/{ecju_query.case_id}/ecju-queries/")

    _notify_exporter_ecju_query_chaser(
        ecju_query.case.submitted_by.email,
        {
            "case_reference": ecju_query.case.reference_code,
            "exporter_frontend_ecju_queries_url": exporter_frontend_ecju_queries_url,
            "remaining_days": 20 - ecju_query.open_working_days,
            "open_working_days": ecju_query.open_working_days,
        },
        callback,
    )


def _notify_exporter_ecju_query(email, data):
    payload = ExporterECJUQuery(**data)
    send_email(email, TemplateType.EXPORTER_ECJU_QUERY, payload)


def _notify_exporter_ecju_query_chaser(email, data, callback):
    payload = ExporterECJUQueryChaser(**data)
    send_email(email, TemplateType.EXPORTER_ECJU_QUERY_CHASER, payload, callback)


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


def notify_exporter_appeal_acknowledgement(case):
    case = case.get_case()
    exporter = case.submitted_by
    payload = ExporterAppealAcknowledgement(
        user_first_name=exporter.first_name,
        application_reference=case.reference_code,
    )
    send_email(exporter.email, TemplateType.EXPORTER_APPEAL_ACKNOWLEDGEMENT, payload)
