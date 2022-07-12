from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterRegistration, ExporterOrganisationApproved
from gov_notify.service import send_email


def notify_exporter_registration(email, data):
    payload = ExporterRegistration(**data)
    send_email(email, TemplateType.EXPORTER_REGISTERED_NEW_ORG, payload)


def notify_exporter_organisation_approved(email, data):
    payload = ExporterOrganisationApproved(**data)
    send_email(email, TemplateType.EXPORTER_ORGANISATION_APPROVED, payload)
