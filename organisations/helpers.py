from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from organisations.enums import OrganisationType, OrganisationStatus


def audit_edited_organisation_fields(user, organisation, new_org):
    if organisation.name != new_org.get("name"):
        audit_trail_service.create(
            actor=user,
            verb=AuditType.UPDATED_ORGANISATION,
            target=organisation,
            payload={
                "organisation_field": "name",
                "previous_value": organisation.name,
                "new_value": new_org.get("name"),
            },
        )
    if organisation.eori_number != new_org.get("eori_number"):
        audit_trail_service.create(
            actor=user,
            verb=AuditType.UPDATED_ORGANISATION,
            target=organisation,
            payload={
                "organisation_field": "EORI number",
                "previous_value": organisation.eori_number,
                "new_value": new_org.get("eori_number"),
            },
        )
    if organisation.sic_number != new_org.get("sic_number") and organisation.type != OrganisationType.HMRC:
        audit_trail_service.create(
            actor=user,
            verb=AuditType.UPDATED_ORGANISATION,
            target=organisation,
            payload={
                "organisation_field": "SIC number",
                "previous_value": organisation.sic_number,
                "new_value": new_org.get("sic_number"),
            },
        )
    if organisation.vat_number != new_org.get("vat_number"):
        audit_trail_service.create(
            actor=user,
            verb=AuditType.UPDATED_ORGANISATION,
            target=organisation,
            payload={
                "organisation_field": "VAT number",
                "previous_value": organisation.vat_number,
                "new_value": new_org.get("vat_number"),
            },
        )
    if (
        organisation.registration_number != new_org.get("registration_number")
        and organisation.type != OrganisationType.HMRC
    ):
        audit_trail_service.create(
            actor=user,
            verb=AuditType.UPDATED_ORGANISATION,
            target=organisation,
            payload={
                "organisation_field": "registration number",
                "previous_value": organisation.registration_number,
                "new_value": new_org.get("registration_number"),
            },
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
    elif decision == OrganisationStatus.REJECTED:
        audit_trail_service.create(
            actor=user,
            verb=AuditType.REJECTED_ORGANISATION,
            target=organisation,
            payload={
                "organisation_name": organisation.name,
            },
        )
