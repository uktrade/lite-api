from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterUserAdded
from gov_notify.service import send_email


def notify_exporter_user_added(email, data):
    payload = ExporterUserAdded(**data)
    send_email(email, TemplateType.EXPORTER_USER_ADDED, payload)
