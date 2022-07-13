from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterRegistration
from gov_notify.service import send_email


def notify_exporter_registration(email, data):
    payload = ExporterRegistration(**data)
    send_email(email, TemplateType.EXPORTER_REGISTERED_NEW_ORG, payload)
