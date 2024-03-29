from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.organisations import notify
from api.organisations.enums import OrganisationType, OrganisationStatus


def add_edited_audit_entry(user, organisation, key, old_value, new_value):
    if old_value == "" or old_value is None:
        old_value = "N/A"
    if new_value == "" or new_value is None:
        new_value = "N/A"

    audit_trail_service.create(
        actor=user,
        verb=AuditType.UPDATED_ORGANISATION,
        target=organisation,
        payload={
            "key": key,
            "old": old_value,
            "new": new_value,
        },
    )


def audit_edited_organisation_fields(user, organisation, new_org, is_non_uk=None):
    if new_org.get("name") and organisation.name != new_org.get("name"):
        add_edited_audit_entry(user, organisation, "name", organisation.name, new_org.get("name"))

    if (
        (organisation.type == OrganisationType.COMMERCIAL and new_org.get("eori_number"))
        or organisation.type != OrganisationType.COMMERCIAL
        or is_non_uk
    ) and organisation.eori_number != new_org.get("eori_number"):

        add_edited_audit_entry(user, organisation, "EORI number", organisation.eori_number, new_org.get("eori_number"))

    if (
        (
            (organisation.type == OrganisationType.COMMERCIAL and new_org.get("sic_number"))
            or organisation.type != OrganisationType.COMMERCIAL
            or is_non_uk
        )
        and organisation.sic_number != new_org.get("sic_number")
        and organisation.type != OrganisationType.HMRC
    ):
        add_edited_audit_entry(user, organisation, "SIC number", organisation.sic_number, new_org.get("sic_number"))

    if (
        (organisation.type == OrganisationType.COMMERCIAL and new_org.get("vat_number"))
        or organisation.type != OrganisationType.COMMERCIAL
        or is_non_uk
    ) and organisation.vat_number != new_org.get("vat_number"):

        add_edited_audit_entry(user, organisation, "VAT number", organisation.vat_number, new_org.get("vat_number"))

    if (
        (
            (organisation.type == OrganisationType.COMMERCIAL and new_org.get("registration_number"))
            or organisation.type != OrganisationType.COMMERCIAL
            or is_non_uk
        )
        and organisation.registration_number != new_org.get("registration_number")
        and organisation.type != OrganisationType.HMRC
    ):
        add_edited_audit_entry(
            user,
            organisation,
            "registration number",
            organisation.registration_number,
            new_org.get("registration_number"),
        )


def audit_reviewed_organisation(user, organisation, decision):

    if decision == OrganisationStatus.ACTIVE:
        audit_trail_service.create(
            actor=user,
            verb=AuditType.APPROVED_ORGANISATION,
            target=organisation,
            payload={
                "organisation_name": organisation.name,
            },
        )
    else:
        audit_trail_service.create(
            actor=user,
            verb=AuditType.REJECTED_ORGANISATION,
            target=organisation,
            payload={
                "organisation_name": organisation.name,
            },
        )


def notify_organisation_reviewed(organisation, decision):
    if decision == OrganisationStatus.ACTIVE:
        notify.notify_exporter_organisation_approved(organisation)
    else:
        notify.notify_exporter_organisation_rejected(organisation)
