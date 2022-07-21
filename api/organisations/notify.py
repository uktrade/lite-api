from django.db.models import F

from api.core.helpers import get_exporter_frontend_url
from gov_notify.enums import TemplateType
from gov_notify.payloads import ExporterRegistration, ExporterOrganisationApproved, ExporterOrganisationRejected
from gov_notify.service import send_email


def notify_exporter_registration(email, data):
    payload = ExporterRegistration(**data)
    send_email(email, TemplateType.EXPORTER_REGISTERED_NEW_ORG, payload)


def _get_organisation_members(organisation):
    return organisation.users.annotate(
        email=F("user__baseuser_ptr__email"), first_name=F("user__baseuser_ptr__first_name")
    ).values_list("email", "first_name")


def notify_exporter_organisation_approved(organisation):
    organisation_members = _get_organisation_members(organisation)
    for email, first_name in organisation_members:
        _notify_exporter_organisation_approved(
            email,
            {
                "exporter_first_name": first_name or "",
                "organisation_name": organisation.name,
                "exporter_frontend_url": get_exporter_frontend_url("/"),
            },
        )


def _notify_exporter_organisation_approved(email, data):
    payload = ExporterOrganisationApproved(**data)
    send_email(email, TemplateType.EXPORTER_ORGANISATION_APPROVED, payload)


def notify_exporter_organisation_rejected(organisation):
    organisation_members = _get_organisation_members(organisation)
    for email, first_name in organisation_members:
        _notify_exporter_organisation_rejected(
            email,
            {
                "exporter_first_name": first_name or "",
                "organisation_name": organisation.name,
            },
        )


def _notify_exporter_organisation_rejected(email, data):
    payload = ExporterOrganisationRejected(**data)
    send_email(email, TemplateType.EXPORTER_ORGANISATION_REJECTED, payload)
