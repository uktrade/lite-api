from django.conf import settings

from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterRegistration, CaseWorkerNewRegistration
from gov_notify.service import send_email


def notify_exporter_registration(email, data):
    payload = ExporterRegistration(**data)
    send_email(email, TemplateType.EXPORTER_REGISTERED_NEW_ORG, payload)


def notify_caseworker_new_registration(data):
    payload = CaseWorkerNewRegistration(**data)
    for email in settings.LITE_INTERNAL_NOTIFICATION_EMAILS.get("CASEWORKER_NEW_REGISTRATION", []):
        send_email(email, TemplateType.CASEWORKER_REGISTERED_NEW_ORG, payload)
