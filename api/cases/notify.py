from api.core.helpers import get_exporter_frontend_url
from api.cases.models import Case, EcjuQuery
from gov_notify.enums import TemplateType
from gov_notify.payloads import (
    ExporterECJUQuery,
    ExporterECJUQueryChaser,
    ExporterLicenceIssued,
    ExporterLicenceRefused,
    ExporterNoLicenceRequired,
    ExporterLicenceRevoked,
    ExporterInformLetter,
    ExporterAppealAcknowledgement,
    ExporterLicenceSuspended,
    ExporterF680OutcomeIssued,
)
from gov_notify.service import send_email


def _notify_exporter_licence_issued(email, data):
    payload = ExporterLicenceIssued(**data)
    send_email(
        email,
        TemplateType.EXPORTER_LICENCE_ISSUED,
        payload,
    )


def notify_exporter_licence_issued(application):
    exporter = application.submitted_by
    case = application.get_case()
    _notify_exporter_licence_issued(
        exporter.email,
        {
            "user_first_name": exporter.first_name,
            "application_reference": case.reference_code,
            "exporter_frontend_url": get_exporter_frontend_url("/"),
        },
    )


def notify_exporter_f680_outcome_issued(application):
    exporter = application.submitted_by
    case = application.get_case()
    _notify_exporter_f680_outcome_issued(
        exporter.email,
        {
            "user_first_name": exporter.first_name,
            "application_reference": case.reference_code,
            "exporter_frontend_url": get_exporter_frontend_url(f"/f680/{application.pk}/summary/generated-documents/"),
        },
    )


def _notify_exporter_f680_outcome_issued(email, data):
    payload = ExporterF680OutcomeIssued(**data)
    send_email(
        email,
        TemplateType.EXPORTER_F680_OUTCOME_ISSUED,
        payload,
    )


def _notify_exporter_licence_refused(email, data):
    payload = ExporterLicenceRefused(**data)
    send_email(
        email,
        TemplateType.EXPORTER_LICENCE_REFUSED,
        payload,
    )


def notify_exporter_licence_refused(application):
    exporter = application.submitted_by
    case = application.get_case()
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
    case = Case.objects.get(pk=case_pk)
    application_manifest = case.get_application_manifest()
    notification_config = application_manifest.notification_config["ecju_query"]
    exporter_frontend_url = get_exporter_frontend_url(notification_config["frontend_url"])
    email_template = notification_config["template"]

    _notify_exporter_ecju_query(
        case.submitted_by.email,
        {
            "exporter_first_name": case.submitted_by.first_name or "",
            "case_reference": case.reference_code,
            "exporter_frontend_url": exporter_frontend_url,
        },
        email_template,
    )


def notify_exporter_ecju_query_chaser(ecju_query_id, callback):
    ecju_query = EcjuQuery.objects.get(id=ecju_query_id)

    application_manifest = ecju_query.case.get_application_manifest()
    notification_config = application_manifest.notification_config["ecju_query_chaser"]
    exporter_frontend_url = get_exporter_frontend_url(
        notification_config["frontend_url"].format(case_id=ecju_query.case_id)
    )
    email_template = notification_config["template"]

    max_days = application_manifest.ecju_max_days

    _notify_exporter_ecju_query_chaser(
        ecju_query.case.submitted_by.email,
        {
            "case_reference": ecju_query.case.reference_code,
            "exporter_frontend_ecju_queries_url": exporter_frontend_url,
            "remaining_days": max_days - ecju_query.open_working_days,
            "open_working_days": ecju_query.open_working_days,
            "exporter_first_name": ecju_query.case.submitted_by.first_name,
        },
        email_template,
        callback,
    )


def _notify_exporter_ecju_query(email, data, email_template):
    payload = ExporterECJUQuery(**data)
    send_email(email, email_template, payload)


def _notify_exporter_ecju_query_chaser(email, data, email_template, callback):
    payload = ExporterECJUQueryChaser(**data)
    send_email(email, email_template, payload, callback)


def _notify_exporter_no_licence_required(email, data):
    payload = ExporterNoLicenceRequired(**data)
    send_email(email, TemplateType.EXPORTER_NO_LICENCE_REQUIRED, payload)


def notify_exporter_no_licence_required(application):
    exporter = application.submitted_by
    case = application.get_case()
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
