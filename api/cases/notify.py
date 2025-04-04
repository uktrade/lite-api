from django.db.models import F

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
)
from gov_notify.service import send_email
from api.cases.enums import CaseTypeEnum


F680_ECJU_QUERY_MAX_DAYS = 30
STANDARD_APPLICATION_ECJU_QUERY_MAX_DAYS = 20


def should_send_ecju_chaser_email(ecju_query):
    if ecju_query.is_f680_query:
        max_days = F680_ECJU_QUERY_MAX_DAYS
    else:
        max_days = STANDARD_APPLICATION_ECJU_QUERY_MAX_DAYS
    return max_days - 5 <= ecju_query.open_working_days <= max_days


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
        .values("id", "email", "first_name", "reference_code", "case_type")
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
        case_info["case_type"],
    )


def notify_exporter_ecju_query_chaser(ecju_query_id, callback):
    ecju_query = EcjuQuery.objects.get(id=ecju_query_id)
    if ecju_query.is_f680_query:
        exporter_frontend_ecju_queries_url = get_exporter_frontend_url(
            f"/f680/{ecju_query.case_id}/summary/ecju-queries/"
        )
        max_days = F680_ECJU_QUERY_MAX_DAYS
    else:
        exporter_frontend_ecju_queries_url = get_exporter_frontend_url(
            f"/applications/{ecju_query.case_id}/ecju-queries/"
        )
        max_days = STANDARD_APPLICATION_ECJU_QUERY_MAX_DAYS

    _notify_exporter_ecju_query_chaser(
        ecju_query.case.submitted_by.email,
        {
            "case_reference": ecju_query.case.reference_code,
            "exporter_frontend_ecju_queries_url": exporter_frontend_ecju_queries_url,
            "remaining_days": max_days - ecju_query.open_working_days,
            "open_working_days": ecju_query.open_working_days,
            "exporter_first_name": ecju_query.case.submitted_by.first_name,
        },
        ecju_query.case.case_type.id,
        callback,
    )


def _notify_exporter_ecju_query(email, data, case_type_id):
    payload = ExporterECJUQuery(**data)
    if str(case_type_id) == str(CaseTypeEnum.F680.id):
        email_template = TemplateType.EXPORTER_F680_ECJU_QUERY
    else:
        email_template = TemplateType.EXPORTER_ECJU_QUERY
    send_email(email, email_template, payload)


def _notify_exporter_ecju_query_chaser(email, data, case_type_id, callback):
    payload = ExporterECJUQueryChaser(**data)
    if str(case_type_id) == str(CaseTypeEnum.F680.id):
        email_template = TemplateType.EXPORTER_F680_ECJU_QUERY_CHASER
    else:
        email_template = TemplateType.EXPORTER_ECJU_QUERY_CHASER
    send_email(email, email_template, payload, callback)


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
